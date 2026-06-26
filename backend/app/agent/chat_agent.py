"""M4 智能问答 ReAct Agent（StateGraph + ToolNode + 标准 ReAct + stream_mode 流式）"""

import asyncio
import re

from langchain_core.messages import AIMessage, AIMessageChunk, SystemMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.chat_tools import (
    search_knowledge_base_tool,
    query_monitoring_data_tool,
    query_knowledge_graph_tool,
    check_water_standard_tool,
)
from app.constants.chat_agent import AGENT_RECURSION_LIMIT
from app.states.chat_agent import ChatAgentState
from app.utils.logger_config import setup_logger
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt

logger = setup_logger(__name__)

_DEGRADED_CONTENT_TRUNCATE = 200
TOOLS = [
    search_knowledge_base_tool,
    query_monitoring_data_tool,
    query_knowledge_graph_tool,
    check_water_standard_tool,
]
tool_node = ToolNode(TOOLS)


async def call_llm(state: ChatAgentState):
    """LLM 决策节点：思考模式 + 流式，逐 token 通过 messages 模式透出 reasoning_content"""
    try:
        raw = state["messages"]
        logger.info(f"call_llm 收到 {len(raw)} 条消息: "
                      f"{[type(m).__name__ + ('(tc)' if getattr(m, 'tool_calls', None) else '') for m in raw]}")

        system_prompt = get_prompt.chat_agent["SYSTEM"]
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(raw)
        model = get_model.build_chat_model(thinking=True).bind_tools(TOOLS)

        full = None
        async for chunk in model.astream(messages):
            full = chunk if full is None else full + chunk

        logger.info(f"call_llm 完成: tool_calls={bool(full.tool_calls)}, "
                      f"content_len={len(full.content or '')}, "
                      f"reasoning_len={len(full.additional_kwargs.get('reasoning_content', '') or '')}")

        progress = []
        if full.tool_calls:
            for tc in full.tool_calls:
                name = tc.get("name", "")
                if name:
                    progress.append({
                        "stage": "tool_call",
                        "tool": name,
                        "tool_call_id": tc.get("id", ""),
                        "args": tc.get("args", {}),
                        "message": f"正在调用{name}..."
                    })
        return {"messages": [full], "progress_snapshot": progress}
    except Exception as e:
        logger.error(f"call_llm 异常: {e}", exc_info=True)
        return {"error": f"LLM 决策失败: {e}"}


def should_continue(state: ChatAgentState) -> str:
    """条件边：error→finalize / tool_calls→continue / 其他→finalize"""
    if state.get("error"):
        return "finalize"
    last_msg = state["messages"][-1] if state.get("messages") else None
    if isinstance(last_msg, (AIMessage, AIMessageChunk)) and last_msg.tool_calls:
        return "continue"
    return "finalize"


def build_chat_graph():
    """编译 M4 ReAct Agent 工作流图（标准 ReAct：call_llm ↔ run_tools，无 tool_calls 时 END）"""
    builder = StateGraph(ChatAgentState)
    builder.add_node("call_llm", call_llm)
    builder.add_node("run_tools", tool_node)
    builder.set_entry_point("call_llm")
    builder.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue": "run_tools",
            "finalize": END,
        },
    )
    builder.add_edge("run_tools", "call_llm")
    return builder.compile()


async def run_chat_agent(query: str, history_messages: list | None = None):
    """执行 Agent，异步生成 dict 事件流（progress / thinking / chunk / done）"""
    graph = build_chat_graph()
    messages = list(history_messages) + [HumanMessage(content=query)] if history_messages else [HumanMessage(content=query)]
    initial_msg_count = len(messages)
    initial = ChatAgentState(
        messages=messages,
        progress_snapshot=None,
        error=None,
    )
    prev_msg_count = len(messages)
    final_state = None

    try:
        async for event in graph.astream(initial, stream_mode=["values", "messages"],
                                          config={"recursion_limit": AGENT_RECURSION_LIMIT}):
            mode, data = event
            if mode == "values":
                final_state = data
                for p in (data.get("progress_snapshot") or []):
                    yield {"type": "progress", **p}
                current_msgs = data.get("messages") or []
                for m in current_msgs[prev_msg_count:]:
                    if isinstance(m, ToolMessage):
                        logger.info(f"tool_result: tool={m.name}, call_id={m.tool_call_id}, "
                                      f"content_len={len(m.content or '')}, preview={(m.content or '')[:60]}")
                        yield {
                            "type": "tool_result",
                            "tool": m.name or "tool",
                            "tool_call_id": m.tool_call_id,
                            "content": (m.content or "")[:500],
                        }
                prev_msg_count = len(current_msgs)
            elif mode == "messages":
                msg, metadata = data
                node = (metadata or {}).get("langgraph_node", "")
                if node == "call_llm":
                    reasoning = msg.additional_kwargs.get("reasoning_content")
                    if reasoning:
                        yield {"type": "thinking", "phase": "explore", "content": reasoning}

        final_text = _get_final_answer_text(final_state)
        if final_text:
            sentences = re.split(r'(?<=[。！？\n.!?])', final_text)
            for s in sentences:
                if s.strip():
                    yield {"type": "chunk", "content": s}
                    await asyncio.sleep(0.02)
        logger.info(f"run_chat_agent 完成: final_text_len={len(final_text)}, "
                      f"final_text_preview={final_text[:100]}...")
        yield {"type": "done", "final_answer": final_text, "state": final_state, "initial_msg_count": initial_msg_count}

    except GraphRecursionError:
        logger.error("Chat Agent 递归超限")
        yield {"type": "progress", "stage": "error", "message": "分析步骤超限，请简化问题"}
        yield {"type": "done", "final_answer": "分析步骤超限", "state": final_state, "initial_msg_count": initial_msg_count}
    except asyncio.TimeoutError:
        logger.error("Chat Agent 执行超时")
        yield {"type": "progress", "stage": "error", "message": "分析超时"}
        yield {"type": "done", "final_answer": "分析超时", "state": final_state, "initial_msg_count": initial_msg_count}
    except asyncio.CancelledError:
        logger.warning("客户端断开连接")
        yield {"type": "progress", "stage": "error", "message": "连接已断开"}
        return
    except Exception as e:
        logger.error(f"Chat Agent 异常: {e}", exc_info=True)
        yield {"type": "progress", "stage": "error", "message": f"分析异常: {e}"}
        yield {"type": "done", "final_answer": "分析异常", "state": final_state, "initial_msg_count": initial_msg_count}


def _get_final_answer_text(state) -> str:
    """从图最终状态中提取 AI 回答文本"""
    if not state:
        return ""
    msgs = state.get("messages") or []
    for m in reversed(msgs):
        if isinstance(m, (AIMessage, AIMessageChunk)) and not m.tool_calls and m.content:
            return m.content
    parts = []
    for m in msgs:
        if isinstance(m, ToolMessage) and m.content:
            parts.append(f"[{m.name}]: {m.content[:_DEGRADED_CONTENT_TRUNCATE]}")
    return "\n".join(parts) if parts else ""
