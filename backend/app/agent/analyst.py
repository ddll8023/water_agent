"""Analyst Agent：ReAct 趋势分析工作流（StateGraph + ToolNode + 双阶段输出）"""

import asyncio
from datetime import datetime, timedelta

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from sqlalchemy import select

from app.agent.analyst_tools import (
    query_reservoir_overview_tool,
    query_monitoring_records_tool,
    neo4j_trace_pollution_tool,
    rag_retrieve_context_tool,
)
from app.constants import agent as constants_agent
from app.core.database import get_background_db_session, commit_or_rollback
from app.models import alert as models_alert
from app.models import patrol_analysis as models_patrol_analysis
from app.models import reservoir as models_reservoir
from app.services import alert_rules as services_alert_rules
from app.services import alerts as services_alerts
from app.states.analysis import ReActAnalystState, AnalystStatus
from app.utils.logger_config import setup_logger
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt

logger = setup_logger(__name__)

TOOLS = [
    query_reservoir_overview_tool,
    query_monitoring_records_tool,
    neo4j_trace_pollution_tool,
    rag_retrieve_context_tool,
]
tool_node = ToolNode(TOOLS)


async def call_llm(state: ReActAnalystState):
    """LLM 决策节点：工具探索阶段，不设 tool_choice，LLM 自由选择"""
    system_prompt = PromptTemplate.from_template(
        get_prompt.alert["REACT_SYSTEM"]
    ).format()
    messages = [SystemMessage(system_prompt)]
    raw = state["messages"]
    if len(raw) > constants_agent.RECENT_MESSAGE_COUNT:
        recent = raw[-constants_agent.RECENT_MESSAGE_COUNT :]
        from langchain_core.messages import ToolMessage

        while recent and isinstance(recent[0], ToolMessage) and len(raw) > len(recent):
            recent = raw[-(len(recent) + 1) :]
        messages.extend(recent)
    else:
        messages.extend(raw)
    model = get_model.build_chat_model(thinking=False).bind_tools(TOOLS)
    response = await model.ainvoke(messages)
    return {"messages": [response]}


def should_continue(state: ReActAnalystState):
    """路由判断：有 tool_calls → 继续循环；无 → 进入最终输出"""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "continue"
    return "finalize"


async def final_answer(state: ReActAnalystState):
    """最终输出节点：纯聊天模型 + 多策略 JSON 解析"""
    system_prompt = PromptTemplate.from_template(
        get_prompt.alert["REACT_SYSTEM"]
    ).format()
    messages = [SystemMessage(system_prompt)] + state["messages"]
    model = get_model.build_chat_model(thinking=False)
    try:
        chain = model | JsonOutputParser(partial=True)
        output = await chain.ainvoke(messages)
        return {"analysis_result": output}
    except OutputParserException:
        pass  # 第一次尝试失败，用纯模型获取输出重新解析
    try:
        from langchain_core.output_parsers.json import parse_json_markdown

        response = await model.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        output = parse_json_markdown(content)
        return {"analysis_result": output}
    except Exception as e2:
        logger.error(f"final_answer JSON 解析失败: {e2}")
        return {"status": AnalystStatus.FAILED, "error": f"最终输出解析失败: {e2}"}


def has_finalized(state: ReActAnalystState):
    """解析后路由：成功→process_alerts，失败→write_summary"""
    if state.get("analysis_result"):
        return "process"
    return "skip"


async def process_alerts(state: ReActAnalystState):
    """创建 AI 趋势预警（source=1），水库级去重后直接创建
    State Key 迁移：原 state["llm_output"] → state["analysis_result"]"""
    analysis_result = state.get("analysis_result")
    if not analysis_result:
        return {"status": AnalystStatus.NO_DATA}

    supplementary_alert_ids = {}
    now = datetime.now()

    reservoir_analyses = analysis_result.get("reservoir_analyses", [])
    if not reservoir_analyses:
        supplementary_alerts = analysis_result.get("supplementary_alerts", [])
        if supplementary_alerts:
            logger.warning(
                "LLM 返回旧格式 supplementary_alerts（无 reservoir_id），跳过预警创建"
            )
            reservoir_analyses = []

    name_to_id = {}
    reservoirs_data = state.get("reservoirs_data") or []
    for rd in reservoirs_data:
        name_to_id[rd.get("reservoir_name", "")] = rd.get("reservoir_id")

    for ra in reservoir_analyses:
        reservoir_id = ra.get("reservoir_id") or name_to_id.get(
            ra.get("reservoir_name", "")
        )
        alerts = ra.get("supplementary_alerts", [])

        if not alerts or not reservoir_id:
            continue

        async with get_background_db_session() as db:
            existing_alerts = (
                await db.scalars(
                    select(models_alert.AlertEvent).where(
                        models_alert.AlertEvent.reservoir_id == reservoir_id,
                        models_alert.AlertEvent.status < 3,
                    )
                )
            ).all()
        existing_indicator_names = set()
        for ea in existing_alerts:
            for ind in ea.indicators or []:
                name = ind.get("name")
                if name:
                    existing_indicator_names.add(name)
        if existing_indicator_names:
            logger.info(
                f"水库 {reservoir_id} 已有未关闭预警覆盖指标: {existing_indicator_names}"
            )

        async with get_background_db_session() as db:
            try:
                reservoir_name = ""
                if reservoir_id:
                    res = await db.get(models_reservoir.Reservoir, reservoir_id)
                    if res:
                        reservoir_name = res.name

                suggestion_tasks = []
                for sa in alerts:
                    indicators = sa.get("indicators", [])
                    if not indicators:
                        continue

                    new_indicators = [
                        ind
                        for ind in indicators
                        if ind.get("name") not in existing_indicator_names
                    ]
                    if not new_indicators:
                        logger.info(
                            f"  ↳ 指标已全部被覆盖，跳过: {sa.get('title', '')}"
                        )
                        continue

                    title = sa.get("title", f"{reservoir_name}AI趋势补充告警")
                    alert_level = sa.get("alert_level", 1)

                    alert_entry = models_alert.AlertEvent(
                        reservoir_id=reservoir_id,
                        title=title,
                        alert_level=alert_level,
                        indicators=new_indicators,
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
                        await services_alert_rules.broadcast_alert(
                            alert_entry, "new_alert"
                        )
                    except Exception:
                        pass
                    try:
                        await services_alert_rules.cache_alert_to_redis(alert_entry)
                    except Exception:
                        pass
                    suggestion_tasks.append(
                        asyncio.create_task(services_alerts.llm_suggestion(alert_id))
                    )
                    supplementary_alert_ids.setdefault(reservoir_id, []).append(
                        alert_id
                    )

                if suggestion_tasks:
                    await asyncio.gather(*suggestion_tasks, return_exceptions=True)

            except Exception as e:
                logger.error(
                    f"process_alerts 异常: reservoir_id={reservoir_id}, error={e}"
                )

    total_alerts = sum(len(v) for v in supplementary_alert_ids.values())
    logger.info(f"process_alerts 完成 → 创建 {total_alerts} 个 AI 预警")
    return {"supplementary_alert_ids": supplementary_alert_ids}


async def write_summary(state: ReActAnalystState):
    """为每个水库写入 patrol_analysis 记录。失败时也写入含 error 字段的记录。
    State Key 迁移：原 state["llm_output"] → state["analysis_result"]"""
    analysis_result = state.get("analysis_result")
    status = state.get("status")
    error = state.get("error")
    reservoir_alert_map = state.get("supplementary_alert_ids", {})

    now = datetime.now()
    period_start_str = state.get("period_start", "")
    period_end_str = state.get("period_end", "")
    period_start = (
        datetime.fromisoformat(period_start_str)
        if period_start_str
        else now - timedelta(hours=6)
    )
    period_end = datetime.fromisoformat(period_end_str) if period_end_str else now

    if not analysis_result or status == AnalystStatus.FAILED:
        summary_text = f"[分析失败] {error or '未知错误'}" if error else "[分析无结果]"
        summary_text = summary_text[: constants_agent.MAX_SUMMARY_LEN]
        async with get_background_db_session() as db:
            try:
                pa = models_patrol_analysis.PatrolAnalysis(
                    reservoir_id=None,
                    analyzed_at=now,
                    period_start=period_start,
                    period_end=period_end,
                    summary=summary_text,
                    supplementary_alert_ids=None,
                )
                db.add(pa)
                await commit_or_rollback(db)
                logger.info(f"analysis failure recorded: id={pa.id}")
            except Exception as e:
                logger.error(f"write_summary 失败记录写入异常: {e}")
        return {"analysis_ids": [], "status": AnalystStatus.FAILED}

    summary_text = (
        analysis_result.get("summary")
        or analysis_result.get("overall", "")
        or "AI 趋势分析完成"
    )
    summary_text = summary_text[: constants_agent.MAX_SUMMARY_LEN]

    reservoir_analyses = analysis_result.get("reservoir_analyses", [])
    if not reservoir_analyses:
        rd_list = []
        async with get_background_db_session() as db:
            rows = (await db.scalars(select(models_reservoir.Reservoir))).all()
            rd_list = [{"reservoir_id": r.id, "reservoir_name": r.name} for r in rows]
        if rd_list:
            reservoir_analyses = [
                {"reservoir_id": rd["reservoir_id"], "summary": summary_text}
                for rd in rd_list
            ]

    name_to_id = {}
    reservoirs_data = state.get("reservoirs_data") or []
    if not reservoirs_data:
        async with get_background_db_session() as db:
            rows = (await db.scalars(select(models_reservoir.Reservoir))).all()
            reservoirs_data = [
                {"reservoir_id": r.id, "reservoir_name": r.name} for r in rows
            ]
    for rd in reservoirs_data:
        name_to_id[rd.get("reservoir_name", "")] = rd.get("reservoir_id")

    written_ids = []

    async with get_background_db_session() as db:
        try:
            for ra in reservoir_analyses:
                reservoir_id = ra.get("reservoir_id") or name_to_id.get(
                    ra.get("reservoir_name", "")
                )
                if reservoir_id is None:
                    continue

                ra_summary = ra.get("summary", summary_text)
                ra_summary = ra_summary[: constants_agent.MAX_SUMMARY_LEN]

                pa = models_patrol_analysis.PatrolAnalysis(
                    reservoir_id=reservoir_id,
                    analyzed_at=now,
                    period_start=period_start,
                    period_end=period_end,
                    summary=ra_summary,
                    supplementary_alert_ids=reservoir_alert_map.get(reservoir_id)
                    or None,
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


def build_react_graph():
    """编译 ReAct Agent 工作流图"""
    builder = StateGraph(ReActAnalystState)

    builder.add_node("call_llm", call_llm)
    builder.add_node("run_tools", tool_node)
    builder.add_node("final_answer", final_answer)
    builder.add_node("process_alerts", process_alerts)
    builder.add_node("write_summary", write_summary)

    builder.set_entry_point("call_llm")

    builder.add_conditional_edges(
        "call_llm",
        should_continue,
        {"continue": "run_tools", "finalize": "final_answer"},
    )
    builder.add_edge("run_tools", "call_llm")
    builder.add_conditional_edges(
        "final_answer",
        has_finalized,
        {"process": "process_alerts", "skip": "write_summary"},
    )
    builder.add_edge("process_alerts", "write_summary")
    builder.add_edge("write_summary", END)

    return builder.compile()


react_graph = None


async def _write_failure_record(now: datetime, summary: str):
    """写入分析失败记录"""
    summary = summary[: constants_agent.MAX_SUMMARY_LEN]
    try:
        async with get_background_db_session() as db:
            pa = models_patrol_analysis.PatrolAnalysis(
                reservoir_id=None,
                analyzed_at=now,
                period_start=now - timedelta(hours=6),
                period_end=now,
                summary=summary,
                supplementary_alert_ids=None,
            )
            db.add(pa)
            await commit_or_rollback(db)
    except Exception as e:
        logger.error(f"写入失败记录异常: {e}")


async def run_analyst_agent():
    """供 APScheduler 调用的 Analyst Agent 入口（签名不变）"""
    global react_graph
    if react_graph is None:
        react_graph = build_react_graph()

    now = datetime.now()
    initial_state: ReActAnalystState = {
        "messages": [
            HumanMessage(
                content=f"请分析 {now.isoformat()} 之前 6h 的所有水库水质趋势数据。"
            )
        ],
        "status": None,
        "period_start": (now - timedelta(hours=6)).isoformat(),
        "period_end": now.isoformat(),
        "reservoirs_data": None,
        "features": None,
        "analysis_result": None,
        "supplementary_alert_ids": None,
        "analysis_ids": None,
        "error": None,
        "start_time": now.isoformat(),
        "duration_ms": None,
    }

    try:
        result = await asyncio.wait_for(
            react_graph.ainvoke(
                initial_state, {"recursion_limit": constants_agent.RECURSION_LIMIT}
            ),
            timeout=constants_agent.TIMEOUT_SECONDS,
        )
        status = result.get("status", AnalystStatus.SUCCESS)
        logger.info(
            f"Analyst Agent 完成: status={status}, "
            f"analysis_ids={result.get('analysis_ids')}"
        )
    except GraphRecursionError:
        logger.error(
            f"Analyst Agent 递归超限（超过 {constants_agent.RECURSION_LIMIT} 步）"
        )
        await _write_failure_record(
            now, f"[分析超限] 超过最大递归步数({constants_agent.RECURSION_LIMIT})"
        )
    except asyncio.TimeoutError:
        logger.error(f"Analyst Agent 执行超时（{constants_agent.TIMEOUT_SECONDS}秒）")
        await _write_failure_record(
            now, f"[执行超时] {constants_agent.TIMEOUT_SECONDS} 秒内未完成"
        )
    except Exception as e:
        logger.error(f"Analyst Agent 异常: {e}", exc_info=True)
        await _write_failure_record(now, f"[分析异常] {e}")
