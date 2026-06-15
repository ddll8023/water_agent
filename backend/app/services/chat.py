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
from langchain_core.prompts import PromptTemplate
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.agent.chat_agent import run_chat_agent


logger = setup_logger(__name__)


async def chat(user_id: int, chat_request: schemas_chat.ChatRequest):
    """对话请求"""
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

        # ── Agent 工具探索阶段 ──
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'agent_plan', 'message': '正在分析问题，规划检索策略...'})}\n\n"
        history_messages = await _load_history_messages(db, session_entity)
        agent_state = None
        process_steps = []
        try:
            async for progress_list, state in run_chat_agent(chat_request.query, history_messages):
                if progress_list:
                    for ev in progress_list:
                        yield f"data: {json.dumps({'type': 'progress', **ev})}\n\n"
                if state is not None:
                    agent_state = state
        except Exception as e:
            logger.warning(f"Agent 异常，降级处理: {e}")

        process_steps = _collect_process_steps(agent_state)
        context = _build_agent_context(agent_state)

        # ── 组装最终 prompt ──
        context_section_parts = []
        if context.get("search_knowledge_base"):
            context_section_parts.append(f"【知识库内容】\n{context['search_knowledge_base']}")
        if context.get("query_monitoring_data"):
            context_section_parts.append(f"【监测数据】\n{context['query_monitoring_data']}")
        if context.get("query_knowledge_graph"):
            context_section_parts.append(f"【图谱信息】\n{context['query_knowledge_graph']}")
        if context.get("check_water_standard"):
            context_section_parts.append(f"【标准限值】\n{context['check_water_standard']}")
        context_section = "\n\n".join(context_section_parts) if context_section_parts else "（本次查询未检索到相关信息，请根据自身专业知识回答）"

        system_prompt = PromptTemplate.from_template(
            get_prompt.chat_agent["CHAT"]["SYSTEM"]
        ).format()
        user_prompt = PromptTemplate.from_template(
            get_prompt.chat_agent["CHAT"]["USER"]
        ).format(
            context_section=context_section,
            history_section=_build_history_section(history_messages),
            query=chat_request.query,
        )

        message_list = [SystemMessage(system_prompt), HumanMessage(user_prompt)]

        yield f"data: {json.dumps({'type': 'progress', 'stage': 'generate', 'message': '正在生成回答...'})}\n\n"

        logger.info(f"LLM 开始生成: session_id={session_entity.id}")

        model = get_model.build_chat_model()
        result = ""
        async for chunk in model.astream(message_list):
            reasoning = chunk.additional_kwargs.get("reasoning_content")
            if reasoning is not None:
                yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning}, ensure_ascii=False)}\n\n"

            if not chunk.content:
                continue

            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
            result += chunk.content
        logger.info(
            f"LLM 生成完成: session_id={session_entity.id} "
            f"response_len={len(result)}"
        )

        new_message_entity = models_chat_message.ChatMessage(
            session_id=session_entity.id,
            role="assistant",
            content=result,
            msg_meta={"process_steps": process_steps} if process_steps else None,
        )
        db.add(new_message_entity)
        await db.flush()

        new_ids = (session_entity.message_list or []).copy()
        new_ids.append(new_message_entity.id)
        session_entity.message_list = new_ids[-SESSION_SLIDING_WINDOW:]

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
        # 复用 Agent 结果：直接重新生成最终回答
        async for chunk in _re_chat_reuse(db, user_id, session_entity, re_chat_request):
            yield chunk
    else:
        # query 变了：完整重新执行
        async for chunk in chat(
            user_id,
            schemas_chat.ChatRequest(
                query=re_chat_request.query, session_id=re_chat_request.session_id
            ),
        ):
            yield chunk


"""辅助函数"""


def _build_agent_context(state) -> dict:
    """从 Agent State 中提取结构化上下文"""
    if state is None:
        return {}
    if isinstance(state, dict):
        return state.get("collected_context") or {}
    if hasattr(state, "get"):
        ctx = state.get("collected_context")
        return ctx if isinstance(ctx, dict) else {}
    return {}


def _build_history_section(history_messages: list) -> str:
    """将历史消息列表转为文本段落"""
    if not history_messages:
        return ""
    parts = ["【历史对话】"]
    for msg in history_messages:
        if msg.role == "user":
            parts.append(f"用户: {msg.content}")
        elif msg.role == "assistant":
            parts.append(f"助手: {msg.content}")
    return "\n".join(parts)


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
            result.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            meta = msg.msg_meta or {}
            result.append(ToolMessage(content=msg.content, tool_call_id=meta.get("tool_call_id", ""), name=meta.get("name", "tool")))
    return result


def _collect_process_steps(agent_state) -> list:
    """从 Agent State 中收集工具调用步骤"""
    if agent_state is None:
        return []
    messages = agent_state.get("messages", []) if isinstance(agent_state, dict) else []
    steps = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            steps.append({
                "type": "tool",
                "name": msg.name or "tool",
                "content": msg.content[:500] if msg.content else "",
            })
    return steps


def _is_query_unchanged(old_query: str, new_query: str) -> bool:
    """判断 query 是否不变（精确字符串匹配）"""
    return old_query == new_query


async def _get_query_by_message_id(db: AsyncSession, message_id: int) -> str:
    """通过 message_id 获取原始用户 query"""
    entity = await db.get(models_chat_message.ChatMessage, message_id)
    return entity.content if entity else ""


async def _re_chat_reuse(db, user_id, session_entity, re_chat_request):
    """复用 Agent 结果：从 msg_meta 提取上下文，直接重新生成最终回答"""
    history = await _load_history_messages(db, session_entity)
    context = {}
    # 新格式：从助手消息 msg_meta.process_steps 提取
    msg_ids = session_entity.message_list or []
    if msg_ids:
        last_assistant = (
            await db.scalars(
                select(models_chat_message.ChatMessage)
                .where(
                    models_chat_message.ChatMessage.id.in_(msg_ids),
                    models_chat_message.ChatMessage.status == 0,
                    models_chat_message.ChatMessage.role == "assistant",
                )
                .order_by(models_chat_message.ChatMessage.created_at.desc())
                .limit(1)
            )
        ).first()
        if last_assistant and last_assistant.msg_meta:
            steps = last_assistant.msg_meta.get("process_steps", [])
            for s in steps:
                if s["type"] == "tool":
                    context[s["name"]] = s["content"]
    # 旧格式兼容：从历史 ToolMessage 提取
    for msg in history:
        if isinstance(msg, ToolMessage):
            context[msg.name or "tool"] = msg.content[:200]

    context_parts = []
    for source, content in context.items():
        context_parts.append(f"【{source}】\n{content}")
    context_section = "\n\n".join(context_parts) if context_parts else "（无检索数据）"

    system_prompt = PromptTemplate.from_template(
        get_prompt.chat_agent["CHAT"]["SYSTEM"]
    ).format()
    user_prompt = PromptTemplate.from_template(
        get_prompt.chat_agent["CHAT"]["USER"]
    ).format(
        context_section=context_section,
        history_section=_build_history_section(history),
        query=re_chat_request.query,
    )
    message_list = [SystemMessage(system_prompt), HumanMessage(user_prompt)]

    yield f"data: {json.dumps({'type': 'progress', 'stage': 'generate', 'message': '正在重新生成回答...'})}\n\n"

    model = get_model.build_chat_model()
    result = ""
    async for chunk in model.astream(message_list):
        reasoning = chunk.additional_kwargs.get("reasoning_content")
        if reasoning is not None:
            yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning}, ensure_ascii=False)}\n\n"
        if not chunk.content:
            continue
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
        result += chunk.content

    new_entity = models_chat_message.ChatMessage(
        session_id=session_entity.id, role="assistant", content=result,
    )
    db.add(new_entity)
    await db.flush()

    new_ids = (session_entity.message_list or []).copy()
    new_ids.append(new_entity.id)
    session_entity.message_list = new_ids[-SESSION_SLIDING_WINDOW:]
    await commit_or_rollback(db)

    yield f"data: {json.dumps({'type': 'done', 'session_id': session_entity.id, 'message_id': new_entity.id}, ensure_ascii=False)}\n\n"
