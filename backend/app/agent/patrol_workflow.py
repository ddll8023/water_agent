from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import PatrolState, PatrolStatus
from app.services import monitoring as services_monitoring
from app.models import alert_rule as models_alert_rule
from app.services.alert_rules import (
    _broadcast_alert,
    _cache_to_redis as cache_alert_to_redis,
)
from app.core.ws_manager import manager
from app.core.database import get_background_db_session, commit_or_rollback
from app.models.patrol_log import PatrolLog
from app.models.patrol_analysis import PatrolAnalysis
from app.models import indicator as models_indicator
from app.models import monitoring as models_monitoring
from app.models import alert as models_alert
from app.models import reservoir as models_reservoir
from app.utils.logger_config import setup_logger
from app.utils.retriever import ensemble_retrieve
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
import json
from app.core.config import settings

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
    need_analyze = False
    target_reservoir_id = None

    if not (result and result.pending_alerts):
        logger.info("process_alerts 完成 → 无待判定数据")
        return {
            "should_analyze": False,
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

            # 3. 查出该水库未关闭的预警（用于合并）
            existing_alerts = (
                await db.scalars(
                    select(models_alert.AlertEvent)
                    .where(
                        and_(
                            models_alert.AlertEvent.reservoir_id == target_reservoir_id,
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
                    cls = rule.trigger_class.lower()
                    if rule.compare_direction == "gt":
                        limit = getattr(ind, f"standard_limit_{cls}_upper", None)
                        if limit is not None and current_value > limit:
                            triggered_entries.append(
                                {"rule": rule, "limit": float(limit)}
                            )
                    else:
                        limit = getattr(ind, f"standard_limit_{cls}_lower", None)
                        if limit is not None and current_value < limit:
                            triggered_entries.append(
                                {"rule": rule, "limit": float(limit)}
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

            if all_entries:
                # 5. 检查已有未关闭预警 → 合并或创建
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
                        try:
                            await _broadcast_alert(existing_alert, "alert_updated")
                        except Exception:
                            pass
                        await cache_alert_to_redis(existing_alert)
                else:
                    title_parts = [f"{e['name']}={e['value']}" for e in all_entries]
                    title = f"{reservoir_name}指标告警（{', '.join(title_parts[:3])}）"
                    new_alert = models_alert.AlertEvent(
                        reservoir_id=target_reservoir_id,
                        title=title,
                        alert_level=max_alert_level,
                        indicators=all_entries,
                        status=0,
                        detected_at=record_time,
                    )
                    db.add(new_alert)
                    await db.flush()
                    await db.refresh(new_alert)
                    try:
                        await _broadcast_alert(new_alert, "new_alert")
                    except Exception:
                        pass
                    await cache_alert_to_redis(new_alert)
            # 6. 判断该水库是否需要 LLM 分析
            try:
                last_time = await db.scalar(
                    select(func.max(PatrolAnalysis.analyzed_at)).where(
                        PatrolAnalysis.reservoir_id == target_reservoir_id
                    )
                )
                if last_time is None:
                    need_analyze = True
                else:
                    elapsed = datetime.now() - last_time
                    if elapsed.total_seconds() > settings.PATROL_ANALYSIS_INTERVAL:
                        need_analyze = True
            except Exception:
                pass

            await commit_or_rollback(db)

        except Exception as e:
            logger.error(f"预警规则判定异常: {e}")
            await db.rollback()

    logger.info(f"process_alerts 完成 → need_analyze={need_analyze}")
    return {
        "should_analyze": need_analyze,
        "target_reservoir_id": target_reservoir_id,
    }


async def llm_analyze(state: PatrolState):
    """Node4: LLM 趋势分析 + 创建补充预警"""
    now = datetime.now()
    period_end = now
    period_start = now - timedelta(hours=12)

    summary_text = ""
    supplementary_alerts = []

    target_reservoir_id = state.get("target_reservoir_id")

    async with get_background_db_session() as db:
        try:
            reservoir = await db.get(models_reservoir.Reservoir, target_reservoir_id)

            indicator_stats = []
            rows = (
                await db.execute(
                    select(
                        models_monitoring.MonitoringRecord.indicator_id,
                        func.avg(models_monitoring.MonitoringRecord.value).label(
                            "avg_value"
                        ),
                        func.max(models_monitoring.MonitoringRecord.value).label(
                            "max_value"
                        ),
                        func.min(models_monitoring.MonitoringRecord.value).label(
                            "min_value"
                        ),
                        func.count(models_monitoring.MonitoringRecord.id).label(
                            "count"
                        ),
                    )
                    .where(
                        models_monitoring.MonitoringRecord.reservoir_id == reservoir.id,
                        models_monitoring.MonitoringRecord.record_time >= period_start,
                        models_monitoring.MonitoringRecord.record_time <= period_end,
                    )
                    .group_by(models_monitoring.MonitoringRecord.indicator_id)
                )
            ).all()
            for row in rows:
                indicator_obj = await db.get(
                    models_indicator.Indicator, row.indicator_id
                )
                if indicator_obj:
                    indicator_stats.append(
                        {
                            "reservoir_name": reservoir.name,
                            "indicator_name": indicator_obj.name,
                            "avg": (
                                float(round(row.avg_value, 2))
                                if row.avg_value
                                else None
                            ),
                            "max": (
                                float(round(row.max_value, 2))
                                if row.max_value
                                else None
                            ),
                            "min": (
                                float(round(row.min_value, 2))
                                if row.min_value
                                else None
                            ),
                            "count": row.count,
                        }
                    )

            recent_alerts = (
                await db.scalars(
                    select(models_alert.AlertEvent)
                    .where(
                        models_alert.AlertEvent.detected_at >= period_start,
                        models_alert.AlertEvent.reservoir_id == reservoir.id,
                    )
                    .order_by(models_alert.AlertEvent.detected_at.desc())
                )
            ).all()

            alert_text = (
                "\n".join([f"[{a.alert_level}] {a.title}" for a in recent_alerts[:20]])
                if recent_alerts
                else "无"
            )

            query_parts = list(
                set(
                    [s["indicator_name"] for s in indicator_stats]
                    + [s["reservoir_name"] for s in indicator_stats]
                )
            )
            query = " ".join(query_parts) + " 水质趋势 分析 异常"
            rag_docs = await ensemble_retrieve(query, top_k=10)
            rag_section = (
                "\n".join(
                    [
                        f"第{i+1}个文档内容：\n{d.page_content}"
                        for i, d in enumerate(rag_docs)
                    ]
                )
                if rag_docs
                else "无相关参考信息"
            )

            system_prompt = PromptTemplate.from_template(
                get_prompt.alert["ANALYSIS"]["SYSTEM"]
            ).format()
            user_prompt = PromptTemplate.from_template(
                get_prompt.alert["ANALYSIS"]["USER"]
            ).format(
                period_start=period_start.strftime("%Y-%m-%d %H:%M"),
                period_end=period_end.strftime("%Y-%m-%d %H:%M"),
                indicator_stats=json.dumps(indicator_stats, ensure_ascii=False),
                alert_summary=alert_text,
                rag_content_section=rag_section,
            )

            model = get_model.build_chat_model(thinking=False)
            chain = model | JsonOutputParser()
            output = await chain.ainvoke(
                [
                    SystemMessage(system_prompt),
                    HumanMessage(user_prompt),
                ]
            )
            summary_text = output.get("overall", "")
            supplementary_alerts = output.get("supplementary_alerts", [])

            if supplementary_alerts:
                all_indicators = []
                for sa in supplementary_alerts:
                    inds = sa.get("indicators", [])
                    for ind in inds:
                        if isinstance(ind, dict) and ind.get("name"):
                            all_indicators.append(ind)

                if not all_indicators:
                    pass
                else:
                    existing = await db.scalar(
                        select(models_alert.AlertEvent).where(
                            and_(
                                models_alert.AlertEvent.reservoir_id == target_reservoir_id,
                                models_alert.AlertEvent.source == 1,
                                models_alert.AlertEvent.status < 3,
                            )
                        ).order_by(models_alert.AlertEvent.detected_at.asc()).limit(1)
                    )

                    if existing:
                        existing_inds = existing.indicators or []
                        existing_names = {x.get("name") for x in existing_inds if x.get("name")}
                        new_inds = [ind for ind in all_indicators if ind.get("name") not in existing_names]
                        if new_inds:
                            existing_inds.extend(new_inds)
                            existing.indicators = existing_inds
                            existing.title = f"{reservoir.name}AI趋势分析补充告警（共{len(existing_inds)}项指标异常）"
                            await db.flush()
                            await db.refresh(existing)
                            try:
                                await _broadcast_alert(existing, "alert_updated")
                            except Exception:
                                pass
                    else:
                        title = f"{reservoir.name}AI趋势分析补充告警（共{len(all_indicators)}项指标异常趋势）"
                        alert_entry = models_alert.AlertEvent(
                            reservoir_id=target_reservoir_id,
                            title=title,
                            alert_level=1,
                            indicators=all_indicators,
                            source=1,
                            status=0,
                            detected_at=now,
                        )
                        db.add(alert_entry)
                        await db.flush()
                        await db.refresh(alert_entry)
                        try:
                            await _broadcast_alert(alert_entry, "new_alert")
                        except Exception:
                            pass

            await commit_or_rollback(db)
        except Exception as e:
            logger.error(f"LLM 分析异常: {e}")
            summary_text = f"分析过程异常：{e}"

    sup_count = len(supplementary_alerts)
    summary_len = len(summary_text) if summary_text else 0
    logger.info(f"llm_analyze 完成 → 摘要长度: {summary_len}, 补充预警: {sup_count}")
    return {
        "analysis_summary": summary_text,
        "supplementary_alerts": supplementary_alerts,
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
        await db.flush()

        analysis_summary = state.get("analysis_summary")
        target_reservoir_id = state.get("target_reservoir_id")
        if analysis_summary and target_reservoir_id:
            period_start_var = now - timedelta(hours=12)
            db.add(
                PatrolAnalysis(
                    reservoir_id=target_reservoir_id,
                    analyzed_at=now,
                    period_start=period_start_var,
                    period_end=now,
                    summary=analysis_summary,
                )
            )

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


def should_analyze(state: PatrolState) -> str:
    """条件路由：process_alerts 后判断是否执行 LLM 分析"""
    if state.get("should_analyze"):
        return "analyze"
    return "skip"


def build_patrol_graph():
    """编译 Patrol 工作流图"""
    builder = StateGraph(PatrolState)

    builder.add_node("fetch_data", fetch_data)
    builder.add_node("process_save", process_save)
    builder.add_node("process_alerts", process_alerts)
    builder.add_node("llm_analyze", llm_analyze)
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
    builder.add_conditional_edges(
        "process_alerts",
        should_analyze,
        {
            "analyze": "llm_analyze",
            "skip": "cache_log",
        },
    )
    builder.add_edge("llm_analyze", "cache_log")
    builder.add_edge("cache_log", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


patrol_graph = None


async def run_patrol_workflow():
    """供 APScheduler 调用的入口函数"""
    global patrol_graph
    if patrol_graph is None:
        patrol_graph = build_patrol_graph()

    initial_state: PatrolState = {
        "status": None,
        "raw_data": None,
        "process_result": None,
        "patrol_log_id": None,
        "error": None,
        "start_time": None,
        "duration_ms": None,
        "should_analyze": None,
        "analysis_summary": None,
        "supplementary_alerts": None,
        "target_reservoir_id": None,
    }

    config = {
        "configurable": {
            "thread_id": f"patrol-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    }

    async for event in patrol_graph.astream(initial_state, config):
        logger.debug(f"Patrol 工作流事件: {event}")
