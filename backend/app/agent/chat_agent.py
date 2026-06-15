"""M4 智能问答 ReAct Agent（StateGraph + ToolNode + astream 流式）"""

import asyncio

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.chat_tools import (
    search_knowledge_base_tool,
    query_monitoring_data_tool,
    query_knowledge_graph_tool,
    check_water_standard_tool,
)
from app.constants.chat_agent import AGENT_RECURSION_LIMIT, AGENT_TIMEOUT_SECONDS
from app.states.chat_agent import ChatAgentState
from app.utils.logger_config import setup_logger
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt

logger = setup_logger(__name__)

TOOLS = [
    search_knowledge_base_tool,
    query_monitoring_data_tool,
    query_knowledge_graph_tool,
    check_water_standard_tool,
]
tool_node = ToolNode(TOOLS)


async def call_llm(state: ChatAgentState):
    """LLM 决策节点：工具探索阶段，不设 tool_choice，LLM 自由选择"""
    try:
        system_prompt = get_prompt.chat_agent["SYSTEM"]
        messages = [SystemMessage(content=system_prompt)]
        raw = state["messages"]
        messages.extend(raw)
        model = get_model.build_chat_model(thinking=False).bind_tools(TOOLS)
        response = await model.ainvoke(messages)
        progress = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                progress.append({
                    "stage": "tool_call",
                    "tool": tc["name"],
                    "message": f"正在调用{tc['name']}..."
                })
        return {"messages": [response], "progress_snapshot": progress}
    except Exception as e:
        logger.error(f"call_llm 异常: {e}", exc_info=True)
        return {"error": f"LLM 决策失败: {e}"}


def should_continue(state: ChatAgentState) -> str:
    """条件边：error→error_exit / tool_calls→continue / 其他→finalize"""
    if state.get("error"):
        return "error_exit"
    last_msg = state["messages"][-1] if state.get("messages") else None
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "continue"
    return "finalize"


async def aggregate_context(state: ChatAgentState):
    """上下文聚合节点：从 messages 中提取各工具的最后结果"""
    progress = [{"stage": "aggregate", "message": "信息聚合完成"}]
    if state.get("error"):
        return {"collected_context": {}, "progress_snapshot": progress}
    context = {}
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            context[msg.name or "tool"] = msg.content
    return {"collected_context": context, "progress_snapshot": progress}


async def handle_error(state: ChatAgentState):
    """异常降级节点：提取已有上下文，不阻塞回答"""
    context = {}
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            context[msg.name or "tool"] = msg.content
    return {"collected_context": context, "progress_snapshot": [{"stage": "error", "message": "部分工具调用异常，使用已有信息"}]}


def build_chat_graph():
    """编译 M4 ReAct Agent 工作流图"""
    builder = StateGraph(ChatAgentState)
    builder.add_node("call_llm", call_llm)
    builder.add_node("run_tools", tool_node)
    builder.add_node("aggregate_context", aggregate_context)
    builder.add_node("handle_error", handle_error)
    builder.set_entry_point("call_llm")
    builder.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue": "run_tools",
            "finalize": "aggregate_context",
            "error_exit": "handle_error",
        },
    )
    builder.add_edge("run_tools", "call_llm")
    builder.add_edge("aggregate_context", END)
    builder.add_edge("handle_error", END)
    return builder.compile()


async def run_chat_agent(query: str, history_messages: list | None = None):
    """执行 Agent，异步生成 (progress_events, final_state) 二元组"""
    graph = build_chat_graph()
    messages = list(history_messages) + [HumanMessage(content=query)] if history_messages else [HumanMessage(content=query)]
    initial = ChatAgentState(
        messages=messages,
        collected_context=None,
        progress_snapshot=None,
        error=None,
    )
    final_state = None
    try:
        async for state_snapshot in graph.astream(initial, {"recursion_limit": AGENT_RECURSION_LIMIT}, stream_mode="values"):
            final_state = state_snapshot
            progress = state_snapshot.get("progress_snapshot")
            if progress:
                yield progress, None
        yield [], final_state or initial
    except GraphRecursionError:
        logger.error("Chat Agent 递归超限")
        ctx = _extract_context(initial)
        yield [{"stage": "error", "message": "分析步骤超限，使用已获取的信息"}], ChatAgentState(
            messages=initial["messages"], collected_context=ctx, error="recursion_limit"
        )
    except asyncio.TimeoutError:
        logger.error("Chat Agent 执行超时")
        ctx = _extract_context(final_state or initial)
        yield [{"stage": "error", "message": "分析超时，使用已获取的信息"}], ChatAgentState(
            messages=(final_state or initial)["messages"], collected_context=ctx, error="timeout"
        )
    except Exception as e:
        logger.error(f"Chat Agent 异常: {e}", exc_info=True)
        ctx = _extract_context(final_state or initial)
        yield [{"stage": "error", "message": f"分析异常: {e}"}], ChatAgentState(
            messages=(final_state or initial)["messages"], collected_context=ctx, error=str(e)
        )


"""辅助函数"""


def _extract_context(state: ChatAgentState) -> dict:
    """从 state 中提取工具调用结果"""
    context = {}
    for msg in state.get("messages", []):
        if isinstance(msg, ToolMessage):
            context[msg.name or "tool"] = msg.content
    return context
