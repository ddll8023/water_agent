"""Analyst Agent：趋势分析工作流，每 6h 对全水库做 LLM 分析"""

import asyncio
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import select, func

from app.agent.state import AnalystState, AnalystStatus
from app.core.database import get_background_db_session, commit_or_rollback
from app.models import reservoir as models_reservoir
from app.models import indicator as models_indicator
from app.models import monitoring as models_monitoring
from app.models import alert as models_alert
from app.models.patrol_analysis import PatrolAnalysis
from app.services.alerts import llm_suggestion
from app.services.alert_rules import broadcast_alert, cache_alert_to_redis
from app.utils.logger_config import setup_logger
from app.utils.retriever import ensemble_retrieve
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

logger = setup_logger(__name__)


async def fetch_recent_data(state: AnalystState):
    """查询所有水库最近 6h 监测数据和预警事件"""
    now = datetime.now()
    period_start = now - timedelta(hours=6)
    start_time = now.isoformat()

    async with get_background_db_session() as db:
        try:
            reservoirs = (await db.scalars(select(models_reservoir.Reservoir))).all()
            if not reservoirs:
                logger.warning("无可用水库，跳过分析")
                return {"status": AnalystStatus.NO_DATA, "start_time": start_time}

            reservoirs_data = []
            for reservoir in reservoirs:
                records = (
                    await db.execute(
                        select(
                            models_monitoring.MonitoringRecord.indicator_id,
                            models_monitoring.MonitoringRecord.value,
                            models_monitoring.MonitoringRecord.record_time,
                        ).where(
                            models_monitoring.MonitoringRecord.reservoir_id == reservoir.id,
                            models_monitoring.MonitoringRecord.record_time >= period_start,
                            models_monitoring.MonitoringRecord.record_time <= now,
                        ).order_by(models_monitoring.MonitoringRecord.record_time.asc())
                    )
                ).all()

                alerts = (
                    await db.scalars(
                        select(models_alert.AlertEvent).where(
                            models_alert.AlertEvent.reservoir_id == reservoir.id,
                            models_alert.AlertEvent.detected_at >= period_start,
                        ).order_by(models_alert.AlertEvent.detected_at.desc())
                    )
                ).all()

                last_analysis = await db.scalar(
                    select(PatrolAnalysis).where(
                        PatrolAnalysis.reservoir_id == reservoir.id,
                    ).order_by(PatrolAnalysis.analyzed_at.desc()).limit(1)
                )

                reservoirs_data.append({
                    "reservoir_id": reservoir.id,
                    "reservoir_name": reservoir.name,
                    "records": [{"indicator_id": r.indicator_id, "value": r.value, "record_time": r.record_time.isoformat()} for r in records],
                    "alerts": [{"id": a.id, "title": a.title, "alert_level": a.alert_level, "detected_at": a.detected_at.isoformat()} for a in alerts],
                    "last_summary": last_analysis.summary if last_analysis else None,
                })

            logger.info(f"fetch_recent_data 完成 → {len(reservoirs_data)} 个水库")
            return {
                "reservoirs_data": reservoirs_data,
                "period_start": period_start.isoformat(),
                "period_end": now.isoformat(),
                "start_time": start_time,
            }
        except Exception as e:
            logger.error(f"fetch_recent_data 异常: {e}")
            return {"status": AnalystStatus.FAILED, "error": str(e), "start_time": start_time}


async def compute_features(state: AnalystState):
    """为每个 (reservoir_id, indicator_id) 计算确定性趋势特征"""
    reservoirs_data = state.get("reservoirs_data")
    if not reservoirs_data:
        return {"status": AnalystStatus.NO_DATA}

    async with get_background_db_session() as db:
        try:
            indicators = (await db.scalars(select(models_indicator.Indicator))).all()
            indicator_map = {ind.id: ind for ind in indicators}

            all_features = []
            for rd in reservoirs_data:
                reservoir_id = rd["reservoir_id"]
                records = rd["records"]

                grouped = {}
                for r in records:
                    grouped.setdefault(r["indicator_id"], []).append(r)

                for indicator_id, recs in grouped.items():
                    values = [r["value"] for r in recs]
                    if not values:
                        continue

                    rec_times = [r["record_time"] for r in recs]
                    first_val = values[0]
                    last_val = values[-1]
                    n = len(values)
                    avg_val = sum(values) / n
                    delta = last_val - first_val
                    delta_percent = (delta / first_val * 100) if first_val != 0 else 0

                    consecutive_rise = 0
                    consecutive_fall = 0
                    max_rise = 0
                    max_fall = 0
                    for i in range(1, n):
                        if values[i] > values[i - 1]:
                            consecutive_rise += 1
                            consecutive_fall = 0
                        elif values[i] < values[i - 1]:
                            consecutive_fall += 1
                            consecutive_rise = 0
                        else:
                            consecutive_rise = 0
                            consecutive_fall = 0
                        max_rise = max(max_rise, consecutive_rise)
                        max_fall = max(max_fall, consecutive_fall)

                    ind = indicator_map.get(indicator_id)
                    all_features.append({
                        "reservoir_id": reservoir_id,
                        "reservoir_name": rd["reservoir_name"],
                        "indicator_id": indicator_id,
                        "indicator_name": ind.name if ind else str(indicator_id),
                        "unit": ind.unit if ind else "",
                        "count": n,
                        "first_value": round(first_val, 4),
                        "last_value": round(last_val, 4),
                        "min": round(min(values), 4),
                        "max": round(max(values), 4),
                        "avg": round(avg_val, 4),
                        "delta": round(delta, 4),
                        "delta_percent": round(delta_percent, 2),
                        "consecutive_rise_count": max_rise,
                        "consecutive_fall_count": max_fall,
                    })

            logger.info(f"compute_features 完成 → {len(all_features)} 个指标特征")
            return {"features": all_features}
        except Exception as e:
            logger.error(f"compute_features 异常: {e}")
            return {"status": AnalystStatus.FAILED, "error": str(e)}


async def ai_trend_analysis(state: AnalystState):
    """LLM 趋势分析，一次性对所有水库生成分析结果"""
    features = state.get("features")
    reservoirs_data = state.get("reservoirs_data")
    if not features or not reservoirs_data:
        return {"status": AnalystStatus.NO_DATA, "llm_output": None}

    period_start = state.get("period_start", "")
    period_end = state.get("period_end", "")

    try:
        query_parts = list(set(
            [f["indicator_name"] for f in features]
            + [f["reservoir_name"] for f in features]
        ))
        query = " ".join(query_parts) + " 水质趋势 分析 异常"
        rag_docs = await ensemble_retrieve(query, top_k=10)
        rag_section = (
            "\n".join(
                [f"第{i+1}个文档内容：\n{d.page_content}" for i, d in enumerate(rag_docs)]
            )
            if rag_docs else "无相关参考信息"
        )

        alert_summary_lines = []
        for rd in reservoirs_data:
            for a in rd.get("alerts", []):
                alert_summary_lines.append(
                    f"[水库{rd['reservoir_id']}][等级{a['alert_level']}] {a['title']}"
                )
        alert_text = "\n".join(alert_summary_lines[:30]) if alert_summary_lines else "无"

        features_by_reservoir = {}
        for f in features:
            features_by_reservoir.setdefault(f["reservoir_name"], []).append(f)

        indicator_stats_text = ""
        for rname, feats in features_by_reservoir.items():
            indicator_stats_text += f"### {rname}\n"
            for f in feats:
                indicator_stats_text += (
                    f"  - {f['indicator_name']}: "
                    f"avg={f['avg']}, max={f['max']}, min={f['min']}, "
                    f"delta={f['delta']}({f['delta_percent']}%), "
                    f"连续上升={f['consecutive_rise_count']}, 连续下降={f['consecutive_fall_count']}, "
                    f"记录数={f['count']}\n"
                )

        system_prompt = PromptTemplate.from_template(
            get_prompt.alert["ANALYSIS"]["SYSTEM"]
        ).format()
        user_prompt = PromptTemplate.from_template(
            get_prompt.alert["ANALYSIS"]["USER"]
        ).format(
            period_start=period_start,
            period_end=period_end,
            indicator_stats=indicator_stats_text,
            alert_summary=alert_text,
            rag_content_section=rag_section,
        )

        model = get_model.build_chat_model(thinking=False)
        chain = model | JsonOutputParser()
        output = await chain.ainvoke([
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ])

        return {"llm_output": output}
    except Exception as e:
        logger.error(f"ai_trend_analysis 异常: {e}", exc_info=True)
        return {"status": AnalystStatus.FAILED, "error": str(e), "llm_output": None}


async def process_alerts(state: AnalystState):
    """创建 AI 趋势预警（source=1），水库级去重后直接创建"""
    llm_output = state.get("llm_output")
    if not llm_output:
        return {"status": AnalystStatus.NO_DATA}

    supplementary_alert_ids = []
    now = datetime.now()

    reservoir_analyses = llm_output.get("reservoir_analyses", [])
    if not reservoir_analyses:
        supplementary_alerts = llm_output.get("supplementary_alerts", [])
        reservoir_analyses = [{"reservoir_id": None, "supplementary_alerts": supplementary_alerts}] if supplementary_alerts else []

    # 构建水库名称→ID 映射（LLM 输出 reservoir_name，需转为 ID）
    name_to_id = {}
    for rd in state.get("reservoirs_data", []):
        name_to_id[rd["reservoir_name"]] = rd["reservoir_id"]

    for ra in reservoir_analyses:
        reservoir_id = ra.get("reservoir_id") or name_to_id.get(ra.get("reservoir_name", ""))
        alerts = ra.get("supplementary_alerts", [])

        if not alerts or not reservoir_id:
            continue

        # 水库级跳过：已有未关闭的 AI 预警则整体跳过
        async with get_background_db_session() as db:
            existing_ai_alert = await db.scalar(
                select(models_alert.AlertEvent).where(
                    models_alert.AlertEvent.reservoir_id == reservoir_id,
                    models_alert.AlertEvent.source == 1,
                    models_alert.AlertEvent.status < 3,
                ).limit(1)
            )
        if existing_ai_alert:
            logger.info(
                f"水库 {reservoir_id} 已有未关闭的 AI 预警 (id={existing_ai_alert.id})，跳过补充预警"
            )
            continue

        async with get_background_db_session() as db:
            try:
                reservoir_name = ""
                if reservoir_id:
                    res = await db.get(models_reservoir.Reservoir, reservoir_id)
                    if res:
                        reservoir_name = res.name

                for sa in alerts:
                    indicators = sa.get("indicators", [])
                    if not indicators:
                        continue

                    title = sa.get("title", f"{reservoir_name}AI趋势补充告警")
                    alert_level = sa.get("alert_level", 1)

                    alert_entry = models_alert.AlertEvent(
                        reservoir_id=reservoir_id,
                        title=title,
                        alert_level=alert_level,
                        indicators=indicators,
                        source=1,
                        status=0,
                        detected_at=now,
                    )
                    db.add(alert_entry)
                    await db.flush()
                    await db.refresh(alert_entry)

                    alert_id = alert_entry.id
                    await commit_or_rollback(db)

                    try:
                        await broadcast_alert(alert_entry, "new_alert")
                    except Exception:
                        pass
                    try:
                        await cache_alert_to_redis(alert_entry)
                    except Exception:
                        pass
                    asyncio.create_task(llm_suggestion(alert_id))
                    supplementary_alert_ids.append(alert_id)

            except Exception as e:
                logger.error(f"process_alerts 异常: reservoir_id={reservoir_id}, error={e}")

    logger.info(f"process_alerts 完成 → 创建 {len(supplementary_alert_ids)} 个 AI 预警")
    return {"supplementary_alert_ids": supplementary_alert_ids}


async def write_summary(state: AnalystState):
    """为每个水库写入 patrol_analysis 记录"""
    llm_output = state.get("llm_output")
    supplementary_alert_ids = state.get("supplementary_alert_ids", [])
    reservoirs_data = state.get("reservoirs_data", [])
    if not llm_output:
        return {"status": AnalystStatus.NO_DATA}

    now = datetime.now()
    period_start_str = state.get("period_start", "")
    period_end_str = state.get("period_end", "")
    period_start = datetime.fromisoformat(period_start_str) if period_start_str else now - timedelta(hours=6)
    period_end = datetime.fromisoformat(period_end_str) if period_end_str else now

    summary_text = llm_output.get("summary") or llm_output.get("overall", "")

    reservoir_analyses = llm_output.get("reservoir_analyses", [])
    if not reservoir_analyses:
        if summary_text and reservoirs_data:
            reservoir_analyses = [{"reservoir_id": rd["reservoir_id"], "summary": summary_text} for rd in reservoirs_data]

    # 构建水库名称→ID 映射（LLM 输出 reservoir_name）
    name_to_id = {}
    for rd in reservoirs_data:
        name_to_id[rd["reservoir_name"]] = rd["reservoir_id"]

    written_ids = []

    async with get_background_db_session() as db:
        try:
            for ra in reservoir_analyses:
                reservoir_id = ra.get("reservoir_id") or name_to_id.get(ra.get("reservoir_name", ""))
                if reservoir_id is None:
                    continue

                pa = PatrolAnalysis(
                    reservoir_id=reservoir_id,
                    analyzed_at=now,
                    period_start=period_start,
                    period_end=period_end,
                    summary=ra.get("summary", summary_text),
                    supplementary_alert_ids=supplementary_alert_ids or None,
                )
                db.add(pa)
                await db.flush()
                written_ids.append(pa.id)

            await commit_or_rollback(db)
            for pid in written_ids:
                logger.info(f"patrol_analysis 写入完成: id={pid}")
        except Exception as e:
            logger.error(f"write_summary 异常: {e}")
            return {"status": AnalystStatus.FAILED, "error": str(e)}

    return {"analysis_ids": written_ids, "status": AnalystStatus.SUCCESS}


def should_fetch(state: AnalystState) -> str:
    """fetch_recent_data 失败或无数据时跳过"""
    status = state.get("status")
    if status in (AnalystStatus.FAILED, AnalystStatus.NO_DATA):
        return "skip"
    return "continue"


def has_features(state: AnalystState) -> str:
    """compute_features 失败或无特征时跳过 LLM"""
    if state.get("features"):
        return "analyze"
    return "skip"


def has_output(state: AnalystState) -> str:
    """LLM 输出为空时跳过预警创建"""
    if state.get("llm_output"):
        return "process"
    return "skip"


def build_analyst_graph():
    """编译 Analyst Agent 工作流图"""
    builder = StateGraph(AnalystState)

    builder.add_node("fetch_recent_data", fetch_recent_data)
    builder.add_node("compute_features", compute_features)
    builder.add_node("ai_trend_analysis", ai_trend_analysis)
    builder.add_node("process_alerts", process_alerts)
    builder.add_node("write_summary", write_summary)

    builder.set_entry_point("fetch_recent_data")

    builder.add_conditional_edges(
        "fetch_recent_data",
        should_fetch,
        {"continue": "compute_features", "skip": END},
    )
    builder.add_conditional_edges(
        "compute_features",
        has_features,
        {"analyze": "ai_trend_analysis", "skip": "write_summary"},
    )
    builder.add_conditional_edges(
        "ai_trend_analysis",
        has_output,
        {"process": "process_alerts", "skip": "write_summary"},
    )
    builder.add_edge("process_alerts", "write_summary")
    builder.add_edge("write_summary", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


analyst_graph = None


async def run_analyst_agent():
    """供 APScheduler 调用的 Analyst Agent 入口"""
    global analyst_graph
    if analyst_graph is None:
        analyst_graph = build_analyst_graph()

    initial_state: AnalystState = {
        "status": None,
        "period_start": None,
        "period_end": None,
        "reservoirs_data": None,
        "features": None,
        "llm_output": None,
        "supplementary_alert_ids": None,
        "analysis_ids": None,
        "error": None,
        "start_time": None,
        "duration_ms": None,
    }

    config = {
        "configurable": {
            "thread_id": f"analyst-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    }

    async for event in analyst_graph.astream(initial_state, config):
        logger.debug(f"Analyst 工作流事件: {event}")
