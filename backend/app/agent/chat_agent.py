"""M4 智能问答 ReAct Agent（StateGraph + ToolNode + 标准 ReAct + stream_mode 流式）"""

import asyncio

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
            # 有 tool_calls 时清空 content，防止 final_answer 误以为已回答
            clean_msg = AIMessage(
                content="",
                tool_calls=full.tool_calls,
                additional_kwargs=full.additional_kwargs,
            )
            return {"messages": [clean_msg], "progress_snapshot": progress}

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


async def final_answer(state: ChatAgentState):
    """最终输出节点：检测 call_llm 是否已产出回答，如有则跳过 LLM 调用"""
    try:
        if state.get("error"):
            return {"final_answer": "", "error": state["error"]}

        raw = state["messages"]

        # 检查 call_llm 最后一轮是否已产出完整回答
        for m in reversed(raw):
            if isinstance(m, (AIMessage, AIMessageChunk)) and not m.tool_calls and len(m.content or '') > 100:
                logger.info(f"final_answer 跳过 LLM，使用已有内容: len={len(m.content)}, preview={m.content[:80]}...")
                return {"final_answer": m.content, "messages": raw + [AIMessage(content=m.content)]}

        logger.info(f"final_answer 调用 LLM 生成...")
        raw = state["messages"]
        logger.info(f"final_answer 收到 {len(raw)} 条消息: "
                      f"{[{'t': type(m).__name__, 'tc': bool(getattr(m, 'tool_calls', None)), 'cl': len(m.content or ''), 'rl': len(m.additional_kwargs.get('reasoning_content', '') or '') if hasattr(m, 'additional_kwargs') else 0} for m in raw]}")

        system_prompt = get_prompt.chat_agent["CHAT"]["SYSTEM"] \
            + "\n\n对话历史中包含工具调用记录和结果，请忽略工具调用过程，直接根据工具返回的结果回答用户问题。"  # TODO: 移入 chat_agent.yaml CHAT.SYSTEM
        start_idx = 1 if raw and isinstance(raw[0], SystemMessage) else 0
        messages = [SystemMessage(content=system_prompt)] + raw[start_idx:]

        model = get_model.build_chat_model()
        full_text = ""
        async for chunk in model.astream(messages):
            full_text += chunk.content

        logger.info(f"final_answer 产出: content_len={len(full_text)}, preview={full_text[:150]}...")
        return {"final_answer": full_text, "messages": raw + [AIMessage(content=full_text)]}
    except Exception as e:
        logger.error(f"final_answer 异常: {e}", exc_info=True)
        return {"final_answer": "", "error": f"最终回答生成失败: {e}"}


def build_chat_graph():
    """编译 M4 ReAct Agent 工作流图"""
    builder = StateGraph(ChatAgentState)
    builder.add_node("call_llm", call_llm)
    builder.add_node("run_tools", tool_node)
    builder.add_node("final_answer", final_answer)
    builder.set_entry_point("call_llm")
    builder.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue": "run_tools",
            "finalize": "final_answer",
        },
    )
    builder.add_edge("run_tools", "call_llm")
    builder.add_edge("final_answer", END)
    return builder.compile()


async def run_chat_agent(query: str, history_messages: list | None = None):
    """执行 Agent，异步生成 dict 事件流（progress / thinking / chunk / done）"""
    graph = build_chat_graph()
    messages = list(history_messages) + [HumanMessage(content=query)] if history_messages else [HumanMessage(content=query)]
    initial = ChatAgentState(
        messages=messages,
        progress_snapshot=None,
        error=None,
        final_answer=None,
    )
    prev_msg_count = len(messages)
    final_state = None
    chunks_yielded = 0

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
                elif node == "final_answer":
                    reasoning = msg.additional_kwargs.get("reasoning_content")
                    if reasoning:
                        yield {"type": "thinking", "phase": "answer", "content": reasoning}
                    if msg.content:
                        chunks_yielded += 1
                        yield {"type": "chunk", "content": msg.content}

        final_text = (final_state or {}).get("final_answer", "")
        if final_text and chunks_yielded == 0:
            import re
            sentences = re.split(r'(?<=[。！？\n])', final_text)
            for s in sentences:
                s = s.strip()
                if s:
                    yield {"type": "chunk", "content": s}
        if not final_text and final_state:
            final_text = _build_degraded_answer(final_state)
            if final_text:
                yield {"type": "chunk", "content": final_text}
        logger.info(f"run_chat_agent 完成: chunks_yielded={chunks_yielded}, "
                      f"final_text_len={len(final_text)}, "
                      f"final_text_preview={final_text[:100]}...")
        yield {"type": "done", "final_answer": final_text, "state": final_state}

    except GraphRecursionError:
        logger.error("Chat Agent 递归超限")
        yield {"type": "progress", "stage": "error", "message": "分析步骤超限，请简化问题"}
        yield {"type": "done", "final_answer": "分析步骤超限", "state": final_state}
    except asyncio.TimeoutError:
        logger.error("Chat Agent 执行超时")
        yield {"type": "progress", "stage": "error", "message": "分析超时"}
        yield {"type": "done", "final_answer": "分析超时", "state": final_state}
    except asyncio.CancelledError:
        logger.warning("客户端断开连接")
        yield {"type": "progress", "stage": "error", "message": "连接已断开"}
        return
    except Exception as e:
        logger.error(f"Chat Agent 异常: {e}", exc_info=True)
        yield {"type": "progress", "stage": "error", "message": f"分析异常: {e}"}
        yield {"type": "done", "final_answer": "分析异常", "state": final_state}


def _build_degraded_answer(state) -> str:
    """降级：从 messages 中提取已有工具结果"""
    parts = []
    for m in (state.get("messages") or []):
        if isinstance(m, ToolMessage) and m.content:
            parts.append(f"[{m.name}]: {m.content[:_DEGRADED_CONTENT_TRUNCATE]}")
    return "\n".join(parts) if parts else "分析异常，无法生成回答"
