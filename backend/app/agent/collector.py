"""Collector Agent：实时采集与规则预警链路，每 10min 运行一次，不调 LLM"""

import asyncio
from datetime import datetime

from sqlalchemy import select, and_, or_
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import PatrolState, PatrolStatus
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

logger = setup_logger(__name__)


async def fetch_data(state: PatrolState):
    """Node1: 获取监测数据（注释切换模拟/真实模式）"""
    start_time = datetime.now()
    try:
        # === 注释切换 True=模拟 False=真实 ===
        MOCK_MODE = True

        if MOCK_MODE:
            record = await services_monitoring._generate_mock_record()
        else:
            record = await services_monitoring._fetch_real_record()

        if not record:
            logger.info("fetch_data 完成 → 无数据")
            return {
                "status": PatrolStatus.NO_DATA,
                "error": "数据获取异常",
                "start_time": start_time.isoformat(),
            }
        ind_fields = [k for k in record if k not in ("station_code", "monitorTime")]
        logger.info(
            f"fetch_data 完成 → 站点: {record.get('station_code')}, 指标: {ind_fields}"
        )
        return {
            "raw_data": record,
            "start_time": start_time.isoformat(),
        }
    except Exception as e:
        logger.error(f"fetch_data 异常 → {e}")
        return {
            "status": PatrolStatus.FAILED,
            "error": f"数据获取异常: {e}",
            "start_time": start_time.isoformat(),
        }


async def process_save(state: PatrolState):
    """Node2: 处理原始数据并入库（不包含预警判定）"""
    async with get_background_db_session() as db:
        try:
            result = await services_monitoring.process_and_save_data(
                db, state["raw_data"]
            )
            await commit_or_rollback(db)

            if result.error_info and result.record_count == 0:
                status_code = PatrolStatus.FAILED
            elif result.error_info:
                status_code = PatrolStatus.PARTIAL
            else:
                status_code = PatrolStatus.SUCCESS

            logger.info(
                f"process_save 完成 → 记录: {result.record_count}, 待判定: {len(result.pending_alerts)}, 状态: {status_code}"
            )
            return {
                "status": status_code,
                "process_result": result,
            }
        except Exception as e:
            logger.error(f"process_save 异常 → {e}")
            return {
                "status": PatrolStatus.FAILED,
                "error": f"入库处理异常: {e}",
            }


async def process_alerts(state: PatrolState):
    """Node3: 批量判定预警规则（一次查出所有数据，内存处理），判断是否需要 LLM 分析"""
    result = state.get("process_result")
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
            for event_type, alert_id, alert_entity in post_commit_actions:
                try:
                    await broadcast_alert(alert_entity, event_type)
                except Exception as e:
                    logger.error(f"广播失败: alert_id={alert_id}, error={e}")
                try:
                    await cache_alert_to_redis(alert_entity)
                except Exception as e:
                    logger.error(f"缓存失败: alert_id={alert_id}, error={e}")
                asyncio.create_task(llm_suggestion(alert_id))

        except Exception as e:
            logger.error(f"预警规则判定异常: {e}")
            await db.rollback()

    logger.info(f"process_alerts 完成 → target_reservoir_id={target_reservoir_id}")
    return {
        "target_reservoir_id": target_reservoir_id,
    }


async def cache_log(state: PatrolState):
    """Node5: 写入 Redis 缓存、巡检日志和分析记录"""
    now = datetime.now()
    result = state.get("process_result")

    if result and result.cached_records:
        for rec in result.cached_records:
            await services_monitoring._cache_to_redis(**rec)

    async with get_background_db_session() as db:
        status_code = state.get("status")
        if status_code is None and result:
            status_code = (
                PatrolStatus.NO_DATA
                if result.record_count == 0
                else PatrolStatus.SUCCESS
            )
        elif status_code is None:
            status_code = PatrolStatus.NO_DATA

        start_time_str = state.get("start_time")
        executed_at = datetime.fromisoformat(start_time_str) if start_time_str else now
        duration_ms = int((now - executed_at).total_seconds() * 1000)

        patrol_entry = PatrolLog(
            executed_at=executed_at,
            status=status_code,
            station_count=result.station_count if result else 0,
            record_count=result.record_count if result else 0,
            new_alert_count=0,
            merge_count=0,
            duration_ms=duration_ms,
            error=state.get("error"),
        )
        db.add(patrol_entry)

        await commit_or_rollback(db)
        await db.refresh(patrol_entry)

        logger.info(
            f"cache_log 完成 → patrol_log_id={patrol_entry.id}, status={status_code}, 耗时={duration_ms}ms"
        )
        return {
            "status": status_code,
            "patrol_log_id": patrol_entry.id,
            "duration_ms": duration_ms,
        }


def should_process(state: PatrolState) -> str:
    """条件路由：fetch_data 失败或无数据时跳过 process_save"""
    status = state.get("status")
    if status in (PatrolStatus.FAILED, PatrolStatus.NO_DATA):
        return "skip"
    return "continue"


def build_collector_graph():
    """编译 Collector Agent 工作流图"""
    builder = StateGraph(PatrolState)

    builder.add_node("fetch_data", fetch_data)
    builder.add_node("process_save", process_save)
    builder.add_node("process_alerts", process_alerts)
    builder.add_node("cache_log", cache_log)

    builder.set_entry_point("fetch_data")

    builder.add_conditional_edges(
        "fetch_data",
        should_process,
        {
            "continue": "process_save",
            "skip": "cache_log",
        },
    )
    builder.add_edge("process_save", "process_alerts")
    builder.add_edge("process_alerts", "cache_log")
    builder.add_edge("cache_log", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


collector_graph = None


async def run_collector_agent():
    """供 APScheduler 调用的 Collector Agent 入口"""
    global collector_graph
    if collector_graph is None:
        collector_graph = build_collector_graph()

    initial_state: PatrolState = {
        "status": None,
        "raw_data": None,
        "process_result": None,
        "patrol_log_id": None,
        "error": None,
        "start_time": None,
        "duration_ms": None,
        "target_reservoir_id": None,
    }

    config = {
        "configurable": {
            "thread_id": f"collector-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    }

    async for event in collector_graph.astream(initial_state, config):
        logger.debug(f"Collector 工作流事件: {event}")
