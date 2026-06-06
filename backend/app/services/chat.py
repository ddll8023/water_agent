import json
import math
import random
import httpx
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, BackgroundTasks
from app.core.database import commit_or_rollback, get_background_db_session
from app.core.redis import redis_client
from app.models import chat_session as models_chat_session
from app.models import chat_message as models_chat_message
from app.utils.logger_config import setup_logger
from app.schemas import chat as schemas_chat
from app.schemas.common import PaginationInfo, PaginatedResponse, ErrorCode
from app.utils.exception import ServiceException
from app.schemas import documents as schemas_documents
from app.models import knowledge_document as models_document
from app.constants import documents as constants_documents
import os
import uuid
from app.utils.file import save_file, ROOT_DIR
from app.core.config import settings
import asyncio
import aiofiles
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.chroma import get_vector_store
from langchain_core.prompts import PromptTemplate
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

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
        vector_store = get_vector_store()
        rag_result_list = await asyncio.to_thread(
            vector_store.similarity_search, query=chat_request.query, k=settings.TOP_K
        )
        logger.info(
            f"知识库检索完成: session_id={session_entity.id} "
            f"result_count={len(rag_result_list)}"
        )

        system_prompt = PromptTemplate.from_template(get_prompt.chat["CHAT"]["SYSTEM"])
        user_prompt = PromptTemplate.from_template(
            get_prompt.chat["CHAT"]["USER"]
        ).format(
            rag_content="\n".join(
                [rag_result.page_content for rag_result in rag_result_list]
            ),
            query=chat_request.query,
        )

        history_message_id_list = session_entity.message_list or []
        if history_message_id_list:
            history_message_list = (
                await db.scalars(
                    select(models_chat_message.ChatMessage)
                    .where(
                        models_chat_message.ChatMessage.id.in_(history_message_id_list),
                        models_chat_message.ChatMessage.status == 0,
                    )
                    .order_by(models_chat_message.ChatMessage.created_at.asc())
                )
            ).all()
        else:
            history_message_list = []
        logger.info(
            f"历史消息加载: session_id={session_entity.id} "
            f"history_count={len(history_message_list)}"
        )

        message_list = []
        message_list.append(SystemMessage(system_prompt.format()))

        for msg in history_message_list:
            if msg.role == "user":
                message_list.append(HumanMessage(msg.content))
            elif msg.role == "assistant":
                message_list.append(AIMessage(msg.content))

        message_list.append(HumanMessage(user_prompt))
        logger.info(f"LLM 开始生成: session_id={session_entity.id}")

        model = get_model.chat_one_model
        result = ""
        async for chunk in model.astream(message_list):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
            result += chunk.content
        logger.info(
            f"LLM 生成完成: session_id={session_entity.id} "
            f"response_len={len(result)}"
        )

        reference: list[dict] = []
        for rag_result in rag_result_list:
            reference.append(
                {
                    "doc_id": rag_result.metadata["doc_id"],
                    "chunk_index": rag_result.metadata["chunk_index"],
                }
            )
        new_message_entity = models_chat_message.ChatMessage(
            session_id=session_entity.id,
            role="assistant",
            content=result,
            reference=reference,
        )
        db.add(new_message_entity)
        await db.flush()
        new_ids = session_entity.message_list.copy() or []
        new_ids.extend([message_entity.id, new_message_entity.id])
        session_entity.message_list = new_ids[-20:]

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
        raise ServiceException(ErrorCode.INTERNAL_ERROR, str(e))
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
    message_entity_list = await db.scalars(
        select(models_chat_message.ChatMessage).where(
            models_chat_message.ChatMessage.id.in_(message_id_list)
        )
    )

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
    old_message_list: list[int] = session_entity.message_list.copy() or []
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
    async for chunk in chat(
        user_id,
        schemas_chat.ChatRequest(
            query=re_chat_request.query, session_id=re_chat_request.session_id
        ),
    ):
        yield chunk
