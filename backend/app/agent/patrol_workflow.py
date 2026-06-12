from datetime import datetime, timedelta
from sqlalchemy import select, func
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import PatrolState
from app.services import monitoring as services_monitoring
from app.services.alert_rules import evaluate_alert_rules
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

logger = setup_logger(__name__)


async def fetch_data(state: PatrolState) -> dict:
    """Node1: 调用外部 API 获取最新监测数据"""
    start_time = datetime.now()
    try:
        raw_data = await services_monitoring._fetch_real_data()
        if not raw_data:
            return {
                **state,
                "status": 3,
                "error": "API 返回空数据",
                "start_time": start_time.isoformat(),
            }
        return {
            **state,
            "raw_data": raw_data,
            "start_time": start_time.isoformat(),
        }
    except Exception as e:
        return {
            **state,
            "status": 2,
            "error": f"API 调用异常: {e}",
            "start_time": start_time.isoformat(),
        }


async def process_save(state: PatrolState) -> dict:
    """Node2: 处理原始数据并入库（不包含预警判定）"""
    async with get_background_db_session() as db:
        try:
            result = await services_monitoring.process_and_save_data(
                db, state["raw_data"]
            )
            await commit_or_rollback(db)

            if result["error_info"] and result["record_count"] == 0:
                status_code = 2
            elif result["error_info"]:
                status_code = 1
            else:
                status_code = 0

            return {
                **state,
                "status": status_code,
                "process_result": result,
            }
        except Exception as e:
            return {
                **state,
                "status": 2,
                "error": f"入库处理异常: {e}",
            }


async def process_alerts(state: PatrolState) -> dict:
    """Node3: 遍历待判定数据，调用预警规则引擎，判断是否需要 LLM 分析"""
    result = state.get("process_result")
    alert_count = 0

    if result and result.get("pending_alerts"):
        async with get_background_db_session() as db:
            try:
                for item in result["pending_alerts"]:
                    indicator = await db.get(
                        models_indicator.Indicator, item["indicator_id"]
                    )
                    if not indicator:
                        continue
                    triggered = await evaluate_alert_rules(
                        db,
                        indicator_id=item["indicator_id"],
                        reservoir_id=item["reservoir_id"],
                        indicator_entity=indicator,
                        current_value=item["value"],
                        record_time=datetime.fromisoformat(item["record_time"]),
                    )
                    if triggered:
                        alert_count += 1
                await commit_or_rollback(db)
            except Exception as e:
                logger.error(f"预警规则判定异常: {e}")

    async with get_background_db_session() as db:
        try:
            last_analysis = await db.scalar(
                select(func.max(PatrolAnalysis.analyzed_at))
            )
            should_analyze = False
            if last_analysis is None:
                should_analyze = True
            else:
                elapsed = datetime.now() - last_analysis
                should_analyze = elapsed.total_seconds() > 12 * 3600
        except Exception:
            should_analyze = False

    return {
        **state,
        "alert_count": alert_count,
        "should_analyze": should_analyze,
    }


async def llm_analyze(state: PatrolState) -> dict:
    """Node4: LLM 趋势分析 + 创建补充预警"""
    now = datetime.now()
    period_end = now
    period_start = now - timedelta(hours=12)

    summary_text = ""
    supplementary_alerts = []

    async with get_background_db_session() as db:
        try:
            reservoirs = (await db.scalars(select(models_reservoir.Reservoir))).all()
            reservoir_names = {r.id: r.name for r in reservoirs}

            indicator_stats = []
            for reservoir in reservoirs:
                rows = (
                    await db.execute(
                        select(
                            models_monitoring.MonitoringRecord.indicator_id,
                            func.avg(models_monitoring.MonitoringRecord.value).label("avg_value"),
                            func.max(models_monitoring.MonitoringRecord.value).label("max_value"),
                            func.min(models_monitoring.MonitoringRecord.value).label("min_value"),
                            func.count(models_monitoring.MonitoringRecord.id).label("count"),
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
                    indicator_obj = await db.get(models_indicator.Indicator, row.indicator_id)
                    if indicator_obj:
                        indicator_stats.append({
                            "reservoir_name": reservoir.name,
                            "indicator_name": indicator_obj.name,
                            "avg": round(row.avg_value, 2) if row.avg_value else None,
                            "max": round(row.max_value, 2) if row.max_value else None,
                            "min": round(row.min_value, 2) if row.min_value else None,
                            "count": row.count,
                        })

            recent_alerts = (
                await db.scalars(
                    select(models_alert.AlertEvent)
                    .where(models_alert.AlertEvent.detected_at >= period_start)
                    .order_by(models_alert.AlertEvent.detected_at.desc())
                )
            ).all()

            alert_text = "\n".join([
                f"[{a.alert_level}] {a.title}" for a in recent_alerts[:20]
            ]) if recent_alerts else "无"

            query_parts = list(set(
                [s["indicator_name"] for s in indicator_stats]
                + [s["reservoir_name"] for s in indicator_stats]
            ))
            query = " ".join(query_parts) + " 水质趋势 分析 异常"
            rag_docs = await ensemble_retrieve(query, top_k=10)
            rag_section = "\n".join(
                [f"第{i+1}个文档内容：\n{d.page_content}" for i, d in enumerate(rag_docs)]
            ) if rag_docs else "无相关参考信息"

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
            output = await chain.ainvoke([
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ])
            summary_text = output.get("overall", "")
            supplementary_alerts = output.get("supplementary_alerts", [])

            for sa in supplementary_alerts:
                reservoir_id = None
                reservoir_code = sa.get("reservoir_code", "")
                for r in reservoirs:
                    if r.code == reservoir_code:
                        reservoir_id = r.id
                        break
                if not reservoir_id:
                    continue
                alert_entry = models_alert.AlertEvent(
                    reservoir_id=reservoir_id,
                    title=sa.get("title", ""),
                    alert_level=1,
                    indicators=sa.get("indicators", []),
                    source=1,
                    status=0,
                    detected_at=now,
                )
                db.add(alert_entry)
                await db.flush()

            await commit_or_rollback(db)
        except Exception as e:
            logger.error(f"LLM 分析异常: {e}")
            summary_text = f"分析过程异常：{e}"

    return {
        **state,
        "analysis_summary": summary_text,
        "supplementary_alerts": supplementary_alerts,
    }


async def cache_log(state: PatrolState) -> dict:
    """Node5: 写入 Redis 缓存、巡检日志和分析记录"""
    now = datetime.now()
    result = state.get("process_result")

    if result and result.get("cached_records"):
        for rec in result["cached_records"]:
            await services_monitoring._cache_to_redis(**rec)

    async with get_background_db_session() as db:
        status_code = state.get("status")
        if status_code is None and result:
            status_code = 3 if result["record_count"] == 0 else 0
        elif status_code is None:
            status_code = 3

        start_time_str = state.get("start_time")
        executed_at = (
            datetime.fromisoformat(start_time_str) if start_time_str else now
        )
        duration_ms = int((now - executed_at).total_seconds() * 1000)

        patrol_entry = PatrolLog(
            executed_at=executed_at,
            status=status_code,
            station_count=result["station_count"] if result else 0,
            record_count=result["record_count"] if result else 0,
            new_alert_count=state.get("alert_count", 0),
            merge_count=0,
            duration_ms=duration_ms,
            error=state.get("error"),
        )
        db.add(patrol_entry)
        await db.flush()

        analysis_summary = state.get("analysis_summary")
        if analysis_summary:
            period_start_var = now - timedelta(hours=12)
            analysis_entry = PatrolAnalysis(
                analyzed_at=now,
                period_start=period_start_var,
                period_end=now,
                summary=analysis_summary,
            )
            db.add(analysis_entry)

        await commit_or_rollback(db)
        await db.refresh(patrol_entry)

        return {
            **state,
            "status": status_code,
            "patrol_log_id": patrol_entry.id,
            "duration_ms": duration_ms,
        }


def should_process(state: PatrolState) -> str:
    """条件路由：fetch_data 失败或无数据时跳过 process_save"""
    status = state.get("status")
    if status in (2, 3):
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
        "alert_count": None,
        "should_analyze": None,
        "analysis_summary": None,
        "supplementary_alerts": None,
    }

    config = {"configurable": {"thread_id": f"patrol-{datetime.now().strftime('%Y%m%d%H%M%S')}"}}

    async for event in patrol_graph.astream(initial_state, config):
        logger.debug(f"Patrol 工作流事件: {event}")
