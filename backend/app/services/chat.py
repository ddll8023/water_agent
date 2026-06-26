"""智能问答对话服务（SSE 流式 + ReAct Agent）"""

import json
import math
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import commit_or_rollback, get_background_db_session
from app.models import chat_session as models_chat_session
from app.models import chat_message as models_chat_message
from app.utils.logger_config import setup_logger
from app.schemas import chat as schemas_chat
from app.schemas.common import PaginationInfo, PaginatedResponse, ErrorCode
from app.utils.exception import ServiceException
from app.constants.chat_agent import SESSION_SLIDING_WINDOW
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from app.agent.chat_agent import run_chat_agent


logger = setup_logger(__name__)


async def chat(user_id: int, chat_request: schemas_chat.ChatRequest):
    """对话请求（事件转发模式：run_chat_agent dict 事件 → SSE 字符串）"""
    logger.info(
        f"对话请求: user_id={user_id} session_id={chat_request.session_id} "
        f"query_len={len(chat_request.query)} query_preview={chat_request.query[:50]}"
    )
    db = get_background_db_session()

    try:
        if chat_request.session_id is None:
            session_entity = models_chat_session.ChatSession(
                user_id=user_id, title=chat_request.query[:30]
            )
            db.add(session_entity)
            await db.flush()
            logger.info(f"新建对话: session_id={session_entity.id} user_id={user_id}")
        else:
            session_entity = await db.get(
                models_chat_session.ChatSession, chat_request.session_id
            )
            if not session_entity:
                logger.warning(
                    f"对话不存在: session_id={chat_request.session_id} user_id={user_id}"
                )
                raise ServiceException(ErrorCode.DATA_NOT_FOUND, "对话不存在")
            logger.info(f"恢复对话: session_id={session_entity.id}")

        message_entity = models_chat_message.ChatMessage(
            session_id=session_entity.id, role="user", content=chat_request.query
        )
        db.add(message_entity)
        await db.flush()

        current_ids = (session_entity.message_list or []).copy()
        current_ids.append(message_entity.id)
        session_entity.message_list = current_ids
        await db.flush()

        # ── Agent 执行（run_chat_agent 内部完成工具探索 + 最终生成）──
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'agent_plan', 'message': '正在分析问题，规划检索策略...'})}\n\n"
        history_messages = await _load_history_messages(db, session_entity)
        final_text = ""
        agent_state = None
        initial_msg_count = 0
        generate_emitted = False

        event_counts = {"progress": 0, "thinking": 0, "chunk": 0, "tool_result": 0}
        try:
            async for ev in run_chat_agent(chat_request.query, history_messages):
                t = ev["type"]
                if t in event_counts:
                    event_counts[t] += 1
                if t == "progress":
                    yield f"data: {json.dumps({'type': 'progress', **{k:v for k,v in ev.items() if k != 'type'}})}\n\n"
                elif t == "thinking":
                    if not generate_emitted:
                        yield f"data: {json.dumps({'type': 'progress', 'stage': 'generate', 'message': '正在生成回答...'})}\n\n"
                        generate_emitted = True
                    yield f"data: {json.dumps({'type': 'thinking', 'content': ev['content'], 'phase': ev.get('phase', 'explore')}, ensure_ascii=False)}\n\n"
                elif t == "chunk":
                    final_text += ev["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': ev['content']}, ensure_ascii=False)}\n\n"
                elif t == "tool_result":
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': ev['tool'], 'tool_call_id': ev.get('tool_call_id', ''), 'content': ev['content']}, ensure_ascii=False)}\n\n"
                elif t == "done":
                    agent_state = ev.get("state")
                    initial_msg_count = ev.get("initial_msg_count", 0)
                    if not final_text:
                        final_text = ev.get("final_answer", "")
        except Exception as e:
            logger.warning(f"Agent 执行异常，降级处理: {e}", exc_info=True)

        logger.info(f"SSE 事件统计: {event_counts}, final_text_len={len(final_text)}, "
                      f"final_text_preview={final_text[:100]}...")

        # 写中间消息（AIMessage tool_calls + ToolMessage），供跨轮对话恢复上下文
        intermediate_ids = []
        if agent_state and initial_msg_count > 0:
            all_msgs = agent_state.get("messages") or []
            new_msgs = all_msgs[initial_msg_count:]
            for m in new_msgs:
                if isinstance(m, AIMessage) and m.tool_calls:
                    tool_calls_data = [
                        tc.model_dump() if hasattr(tc, 'model_dump') else tc
                        for tc in m.tool_calls
                    ]
                    helper = models_chat_message.ChatMessage(
                        session_id=session_entity.id,
                        role="assistant",
                        content=m.content or "",
                        msg_meta={"tool_calls": tool_calls_data},
                    )
                    db.add(helper)
                    intermediate_ids.append(helper.id)
                elif isinstance(m, ToolMessage):
                    helper = models_chat_message.ChatMessage(
                        session_id=session_entity.id,
                        role="tool",
                        content=(m.content or "")[:500],
                        msg_meta={"tool_call_id": m.tool_call_id, "name": m.name or "tool"},
                    )
                    db.add(helper)
                    intermediate_ids.append(helper.id)

        process_steps = _extract_process_steps_from_messages(agent_state)
        thinking_rounds = _extract_thinking_rounds_from_messages(agent_state)

        new_message_entity = models_chat_message.ChatMessage(
            session_id=session_entity.id,
            role="assistant",
            content=final_text,
            msg_meta={
                "process_steps": process_steps,
                "thinkingRounds": thinking_rounds,
            } if process_steps or thinking_rounds else None,
        )
        db.add(new_message_entity)
        await db.flush()

        new_ids = (session_entity.message_list or []).copy()
        new_ids.extend(intermediate_ids)
        new_ids.append(new_message_entity.id)
        session_entity.message_list = new_ids[-SESSION_SLIDING_WINDOW:]
        logger.info(f"对话消息落库: session_id={session_entity.id}, "
                      f"intermediate_ids={intermediate_ids}, final_id={new_message_entity.id}, "
                      f"total_in_window={len(new_ids)}")

        await commit_or_rollback(db)
        logger.info(
            f"对话完成: session_id={session_entity.id} " f"message_count={len(new_ids)}"
        )
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_entity.id, 'message_id': new_message_entity.id, 'user_message_id': message_entity.id}, ensure_ascii=False)}\n\n"
    except Exception as e:
        await db.rollback()
        logger.error(
            f"对话异常: user_id={user_id} session_id={chat_request.session_id} "
            f"error={e}",
            exc_info=True,
        )
        raise ServiceException(ErrorCode.INTERNAL_ERROR, "对话处理失败")
    finally:
        await db.close()


async def get_chat_list(
    db: AsyncSession, get_chat_list_request: schemas_chat.GetChatListRequest
):
    """获取对话列表请求"""
    total = await db.scalar(select(func.count(models_chat_session.ChatSession.id)))
    chat_entity_list = (
        await db.scalars(
            select(models_chat_session.ChatSession)
            .order_by(models_chat_session.ChatSession.updated_at.desc())
            .offset(get_chat_list_request.page_size * (get_chat_list_request.page - 1))
            .limit(get_chat_list_request.page_size)
        )
    ).all()
    return PaginatedResponse(
        lists=[
            schemas_chat.GetChatListResponse.model_validate(chat_entity)
            for chat_entity in chat_entity_list
        ],
        pagination=PaginationInfo(
            page=get_chat_list_request.page,
            page_size=get_chat_list_request.page_size,
            total=total,
            total_pages=math.ceil(total / get_chat_list_request.page_size),
        ),
    )


async def get_chat_detail(db: AsyncSession, session_id: int):
    """获取对话详情请求"""
    session_entity = await db.get(models_chat_session.ChatSession, session_id)
    if session_entity is None:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "会话不存在")
    message_id_list = session_entity.message_list
    message_entity_list = (
        await db.scalars(
            select(models_chat_message.ChatMessage).where(
                models_chat_message.ChatMessage.id.in_(message_id_list),
                models_chat_message.ChatMessage.status == 0,
                models_chat_message.ChatMessage.role != "tool",
            )
        )
    ).all()
    # 过滤掉中间助理消息（带 tool_calls 的 AIMessage，content 通常为空）
    message_entity_list = [
        m for m in message_entity_list
        if not (m.role == "assistant" and (m.msg_meta or {}).get("tool_calls"))
    ]

    return schemas_chat.GetChatDetailResponse(
        id=session_id,
        title=session_entity.title,
        created_at=session_entity.created_at,
        updated_at=session_entity.updated_at,
        messages=[
            schemas_chat.ChatItem.model_validate(message_entity)
            for message_entity in message_entity_list
        ],
    )


async def delete_chat(db: AsyncSession, session_id: int):
    """删除对话"""
    session_entity = await db.get(models_chat_session.ChatSession, session_id)
    if not session_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "对话不存在")
    await db.delete(session_entity)
    await commit_or_rollback(db)
    return True


async def re_chat(
    db: AsyncSession, user_id, re_chat_request: schemas_chat.ReChatRequest
):
    """重试/修改对话"""
    session_entity = await db.get(
        models_chat_session.ChatSession, re_chat_request.session_id
    )
    if not session_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "对话不存在")

    old_message_list: list[int] = (session_entity.message_list or []).copy()
    re_message_index = old_message_list.index(re_chat_request.message_id)
    new_message_list = old_message_list[:re_message_index]
    delete_message_list = old_message_list[re_message_index:]

    await db.execute(
        update(models_chat_message.ChatMessage)
        .where(models_chat_message.ChatMessage.id.in_(delete_message_list))
        .values(status=1)
    )
    session_entity.message_list = new_message_list
    await commit_or_rollback(db)

    old_query = await _get_query_by_message_id(db, re_chat_request.message_id)
    if _is_query_unchanged(old_query, re_chat_request.query):
        async for chunk in _re_chat_reuse(db, user_id, session_entity, re_chat_request):
            yield chunk
    else:
        async for chunk in chat(
            user_id,
            schemas_chat.ChatRequest(
                query=re_chat_request.query, session_id=re_chat_request.session_id
            ),
        ):
            yield chunk


"""辅助函数"""


def _extract_process_steps_from_messages(state) -> list:
    """从 agent state 的 messages 中提取工具调用步骤（含参数和结果）"""
    if state is None:
        return []
    # 第一遍：收集所有 AIMessage 中的 tool_calls，按 id 索引
    tool_call_args: dict[str, dict] = {}
    for m in (state.get("messages") or []):
        if isinstance(m, (AIMessage, AIMessageChunk)) and m.tool_calls:
            for tc in m.tool_calls:
                tc_id = tc.get("id", "")
                if tc_id:
                    tool_call_args[tc_id] = tc.get("args", {})

    # 第二遍：为每个 ToolMessage 补上 args
    steps = []
    for m in (state.get("messages") or []):
        if isinstance(m, ToolMessage):
            tc_id = m.tool_call_id or ""
            args = tool_call_args.get(tc_id, {})
            steps.append({
                "type": "tool",
                "name": m.name or "tool",
                "args": args,
                "content": m.content[:500] if m.content else "",
            })
    return steps


def _extract_thinking_rounds_from_messages(state):
    """从 agent state messages 中提取思考过程轮次（含推理内容和工具名）"""
    if state is None:
        return []
    msgs = state.get("messages") or []
    rounds = []
    current_round = None
    for m in msgs:
        if isinstance(m, (AIMessage, AIMessageChunk)):
            reasoning = m.additional_kwargs.get("reasoning_content")
            if reasoning:
                if current_round is None:
                    current_round = {"thinking": "", "tools": []}
                current_round["thinking"] += reasoning
            if getattr(m, "tool_calls", None):
                if current_round is None:
                    current_round = {"thinking": "", "tools": []}
                for tc in m.tool_calls:
                    name = tc.get("name", "")
                    if name and name not in current_round["tools"]:
                        current_round["tools"].append(name)
                if current_round:
                    rounds.append(current_round)
                    current_round = None
    if current_round and current_round["thinking"]:
        rounds.append(current_round)
    return rounds


async def _load_history_messages(db, session_entity) -> list:
    """从 chat_message 表加载历史消息"""
    msg_ids = (session_entity.message_list or [])[:-1]
    if not msg_ids:
        return []
    history_list = (
        await db.scalars(
            select(models_chat_message.ChatMessage).where(
                models_chat_message.ChatMessage.id.in_(msg_ids),
                models_chat_message.ChatMessage.status == 0,
            ).order_by(models_chat_message.ChatMessage.created_at.asc())
        )
    ).all()
    result = []
    for msg in history_list:
        if msg.role == "user":
            result.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            meta = msg.msg_meta or {}
            if meta.get("tool_calls"):
                result.append(AIMessage(content=msg.content, tool_calls=meta["tool_calls"]))
            else:
                result.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            meta = msg.msg_meta or {}
            result.append(ToolMessage(content=msg.content, tool_call_id=meta.get("tool_call_id", ""), name=meta.get("name", "tool")))
    return result


def _is_query_unchanged(old_query: str, new_query: str) -> bool:
    """判断 query 是否不变（精确字符串匹配）"""
    return old_query == new_query


async def _get_query_by_message_id(db: AsyncSession, message_id: int) -> str:
    """通过 message_id 获取原始用户 query"""
    entity = await db.get(models_chat_message.ChatMessage, message_id)
    return entity.content if entity else ""


async def _re_chat_reuse(db, user_id, session_entity, re_chat_request):
    """重新生成：从历史消息重建完整消息序列，跳过 Agent Graph 工具循环"""
    history = await _load_history_messages(db, session_entity)
    system_prompt = get_prompt.chat_agent["CHAT"]["SYSTEM"]
    messages = [SystemMessage(content=system_prompt)] + history

    user_msg = models_chat_message.ChatMessage(
        session_id=session_entity.id, role="user", content=re_chat_request.query
    )
    db.add(user_msg)
    await db.flush()
    session_entity.message_list = (session_entity.message_list or []) + [user_msg.id]

    yield f"data: {json.dumps({'type': 'progress', 'stage': 'generate', 'message': '正在重新生成回答...'})}\n\n"

    model = get_model.build_chat_model()
    result = ""
    thinking_rounds = []
    async for chunk in model.astream(messages):
        reasoning = chunk.additional_kwargs.get("reasoning_content")
        if reasoning is not None:
            if not thinking_rounds:
                thinking_rounds.append({"thinking": "", "tools": []})
            thinking_rounds[-1]["thinking"] += reasoning
            yield f"data: {json.dumps({'type': 'thinking', 'phase': 'answer', 'content': reasoning}, ensure_ascii=False)}\n\n"
        if not chunk.content:
            continue
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
        result += chunk.content

    new_entity = models_chat_message.ChatMessage(
        session_id=session_entity.id,
        role="assistant",
        content=result,
        msg_meta={"thinkingRounds": thinking_rounds} if thinking_rounds else None,
    )
    db.add(new_entity)
    await db.flush()

    new_ids = (session_entity.message_list or []).copy()
    new_ids.append(new_entity.id)
    session_entity.message_list = new_ids[-SESSION_SLIDING_WINDOW:]
    await commit_or_rollback(db)

    yield f"data: {json.dumps({'type': 'done', 'session_id': session_entity.id, 'message_id': new_entity.id, 'user_message_id': user_msg.id}, ensure_ascii=False)}\n\n"
