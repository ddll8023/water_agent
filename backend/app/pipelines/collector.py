"""Collector 采集管道：实时采集与规则预警链路，每 10min 运行一次，不调 LLM"""

import asyncio
from datetime import datetime

from sqlalchemy import select, and_, or_
from app.states.patrol import PatrolStatus
from app.states.monitoring import ProcessResult
from app.services.alert_rules import _evaluate_rule_trigger
from app.services.alerts import llm_suggestion
from app.services import monitoring as services_monitoring
from app.models import alert_rule as models_alert_rule
from app.services.alert_rules import (
    broadcast_alert,
    cache_alert_to_redis,
)
from app.core.database import get_background_db_session, commit_or_rollback
from app.models.patrol_log import PatrolLog
from app.models import indicator as models_indicator
from app.models import alert as models_alert
from app.models import reservoir as models_reservoir
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException

logger = setup_logger(__name__)


async def fetch_data():
    """从外部 API 采集最新监测数据"""
    try:
        # === 注释切换 True=模拟 False=真实 ===
        MOCK_MODE = True

        if MOCK_MODE:
            record = await services_monitoring._generate_mock_record()
        else:
            record = await services_monitoring._fetch_real_record()

        if not record:
            return None
        ind_fields = [k for k in record if k not in ("station_code", "monitorTime")]
        logger.info(
            f"fetch_data 完成 → 站点: {record.get('station_code')}, 指标: {ind_fields}"
        )
        return record
    except Exception as e:
        logger.error(f"fetch_data 异常 → {e}")
        return None


async def process_save(raw_data):
    """处理原始数据并入库"""
    async with get_background_db_session() as db:
        try:
            result = await services_monitoring.process_and_save_data(
                db, raw_data
            )
            await commit_or_rollback(db)

            logger.info(
                f"process_save 完成 → 记录: {result.record_count}, 待判定: {len(result.pending_alerts)}, error_info: {result.error_info}"
            )
            return result
        except Exception as e:
            logger.error(f"process_save 异常 → {e}")
            return ProcessResult(
                station_count=0, record_count=0,
                pending_alerts=[], cached_records=[],
                error_info="入库处理异常",
            )


async def process_alerts(result):
    """批量判定预警规则，创建/合并预警"""
    target_reservoir_id = None

    if not (result and result.pending_alerts):
        logger.info("process_alerts 完成 → 无待判定数据")
        return {
            "target_reservoir_id": None,
        }

    target_reservoir_id = result.pending_alerts[0]["reservoir_id"]

    async with get_background_db_session() as db:
        try:
            # 1. 批量查出所有指标对象
            indicator_ids = list(
                {item["indicator_id"] for item in result.pending_alerts}
            )
            indicators = (
                await db.scalars(
                    select(models_indicator.Indicator).where(
                        models_indicator.Indicator.id.in_(indicator_ids)
                    )
                )
            ).all()
            indicator_map = {ind.id: ind for ind in indicators}

            # 2. 批量查出该水库所有匹配的活跃规则
            all_rules = (
                await db.scalars(
                    select(models_alert_rule.AlertRule).where(
                        and_(
                            models_alert_rule.AlertRule.indicator_id.in_(indicator_ids),
                            models_alert_rule.AlertRule.is_active == 1,
                            or_(
                                models_alert_rule.AlertRule.reservoir_id
                                == target_reservoir_id,
                                models_alert_rule.AlertRule.reservoir_id.is_(None),
                            ),
                        )
                    )
                )
            ).all()
            # 水库级规则优先，全局规则兜底
            reservoir_rules_map = {}
            global_rules_map = {}
            for rule in all_rules:
                if rule.reservoir_id == target_reservoir_id:
                    reservoir_rules_map.setdefault(rule.indicator_id, []).append(rule)
                else:
                    global_rules_map.setdefault(rule.indicator_id, []).append(rule)

            # 3. 查出该水库未关闭的规则预警（用于合并，只合并 source=0）
            existing_alerts = (
                await db.scalars(
                    select(models_alert.AlertEvent)
                    .where(
                        and_(
                            models_alert.AlertEvent.reservoir_id == target_reservoir_id,
                            models_alert.AlertEvent.source == 0,
                            models_alert.AlertEvent.status < 3,
                        )
                    )
                    .order_by(models_alert.AlertEvent.detected_at.asc())
                )
            ).all()

            reservoir = await db.get(models_reservoir.Reservoir, target_reservoir_id)
            reservoir_name = reservoir.name if reservoir else target_reservoir_id

            # 4. 内存判定所有指标，收集触发条目
            record_time = None
            all_entries = []
            max_alert_level = 0

            for item in result.pending_alerts:
                ind = indicator_map.get(item["indicator_id"])
                if not ind:
                    continue

                rules = reservoir_rules_map.get(item["indicator_id"], [])
                if not rules:
                    rules = global_rules_map.get(item["indicator_id"], [])

                current_value = item["value"]
                record_time = datetime.fromisoformat(item["record_time"])

                triggered_entries = []
                for rule in rules:
                    triggered, limit = _evaluate_rule_trigger(rule, ind, current_value)
                    if triggered:
                        triggered_entries.append(
                            {"rule": rule, "limit": limit}
                        )

                if not triggered_entries:
                    continue

                max_entry = max(triggered_entries, key=lambda x: x["rule"].alert_level)
                rule = max_entry["rule"]
                limit = max_entry["limit"]

                all_entries.append(
                    {
                        "indicator_id": item["indicator_id"],
                        "name": ind.name,
                        "value": current_value,
                        "limit": limit,
                        "unit": ind.unit or "",
                    }
                )
                max_alert_level = max(max_alert_level, rule.alert_level)

            post_commit_actions = []

            if all_entries:
                existing_alert = existing_alerts[0] if existing_alerts else None

                if existing_alert:
                    existing_inds = existing_alert.indicators or []
                    existing_ids = {x.get("indicator_id") for x in existing_inds}
                    new_entries = [
                        e for e in all_entries if e["indicator_id"] not in existing_ids
                    ]

                    if new_entries:
                        existing_inds.extend(new_entries)
                        existing_alert.indicators = existing_inds
                        existing_alert.alert_level = max(
                            existing_alert.alert_level, max_alert_level
                        )
                        existing_alert.title = f"{reservoir_name}多指标复合告警（共{len(existing_inds)}项指标异常）"
                        await db.flush()
                        await db.refresh(existing_alert)
                        post_commit_actions.append(
                            ("alert_updated", existing_alert.id, existing_alert)
                        )
                else:
                    title_parts = [f"{e['name']}={e['value']}" for e in all_entries]
                    title = f"{reservoir_name}指标告警（{', '.join(title_parts[:3])}）"
                    new_alert = models_alert.AlertEvent(
                        reservoir_id=target_reservoir_id,
                        title=title,
                        alert_level=max_alert_level,
                        indicators=all_entries,
                        status=0,
                        source=0,
                        detected_at=record_time,
                    )
                    db.add(new_alert)
                    await db.flush()
                    await db.refresh(new_alert)
                    post_commit_actions.append(
                        ("new_alert", new_alert.id, new_alert)
                    )

                await commit_or_rollback(db)

            # 在 commit 成功后执行外部副作用
            suggestion_tasks = []
            for event_type, alert_id, alert_entity in post_commit_actions:
                try:
                    await broadcast_alert(alert_entity, event_type)
                except Exception as e:
                    logger.error(f"广播失败: alert_id={alert_id}, error={e}")
                try:
                    await cache_alert_to_redis(alert_entity)
                except Exception as e:
                    logger.error(f"缓存失败: alert_id={alert_id}, error={e}")
                suggestion_tasks.append(asyncio.create_task(llm_suggestion(alert_id)))
            if suggestion_tasks:
                await asyncio.gather(*suggestion_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"预警规则判定异常: {e}")
            await db.rollback()

    logger.info(f"process_alerts 完成 → target_reservoir_id={target_reservoir_id}")
    return {
        "target_reservoir_id": target_reservoir_id,
    }


async def cache_log(result, status, start_time, error=None):
    """写入 Redis 缓存和巡检日志"""
    now = datetime.now()

    if result and result.cached_records:
        for rec in result.cached_records:
            await services_monitoring._cache_to_redis(**rec)

    async with get_background_db_session() as db:
        if status is None and result:
            status = (
                PatrolStatus.NO_DATA
                if result.record_count == 0
                else PatrolStatus.SUCCESS
            )
        elif status is None:
            status = PatrolStatus.NO_DATA

        executed_at = datetime.fromisoformat(start_time) if start_time else now
        duration_ms = int((now - executed_at).total_seconds() * 1000)

        patrol_entry = PatrolLog(
            executed_at=executed_at,
            status=status,
            station_count=result.station_count if result else 0,
            record_count=result.record_count if result else 0,
            new_alert_count=0,
            merge_count=0,
            duration_ms=duration_ms,
            error=error,
        )
        db.add(patrol_entry)

        await commit_or_rollback(db)
        await db.refresh(patrol_entry)

        logger.info(
            f"cache_log 完成 → patrol_log_id={patrol_entry.id}, status={status}, 耗时={duration_ms}ms"
        )


async def run_collector_agent():
    """采集管道入口：APScheduler 每 10 分钟调用"""
    start_time = datetime.now().isoformat()
    try:
        raw_data = await fetch_data()
        if not raw_data:
            await cache_log(None, PatrolStatus.NO_DATA, start_time, "无采集数据")
            return

        result = await process_save(raw_data)

        if result.error_info and result.record_count == 0:
            await cache_log(result, PatrolStatus.FAILED, start_time, result.error_info)
            return
        if result.error_info:
            await process_alerts(result)
            await cache_log(result, PatrolStatus.PARTIAL, start_time, result.error_info)
            return

        await process_alerts(result)
        await cache_log(result, PatrolStatus.SUCCESS, start_time)

    except ServiceException as e:
        logger.error(f"采集管道业务异常: error={e.message}")
        await cache_log(None, PatrolStatus.FAILED, start_time, e.message)
    except Exception as exc:
        logger.error(f"采集管道系统异常: error={exc}", exc_info=True)
        await cache_log(None, PatrolStatus.FAILED, start_time, "系统内部错误")
