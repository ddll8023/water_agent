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
from app.schemas import documents as schemas_documents
from app.constants import documents as constants_documents
from app.core.config import settings
import asyncio
from app.core.chroma import get_vector_store
from langchain_core.prompts import PromptTemplate
from app.utils.prompt_factory import get_prompt
from app.utils.model_factory import get_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser

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

        yield f"data: {json.dumps({'type': 'progress', 'stage': 'intent', 'message': '正在识别意图...'})}\n\n"
        intent_results = await _identify_intent(chat_request.query)

        task_map: dict[str, any] = {}
        stage_names = {
            "rag": ("retrieval", "正在检索知识库..."),
            "mysql": ("mysql_query", "正在查询监测数据..."),
            "graph": ("graph_query", "正在查询知识图谱..."),
        }

        if "rag" in intent_results:
            task_map["rag"] = _rag_retriever(intent_results["rag"])

        for tool_name in task_map:
            stage, msg = stage_names.get(
                tool_name, (tool_name, f"正在执行{tool_name}查询...")
            )
            yield f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': msg})}\n\n"

        task_results: dict[str, any] = {}
        if task_map:
            raw_results = await asyncio.gather(
                *task_map.values(), return_exceptions=True
            )
            task_results = dict(zip(task_map.keys(), raw_results))
        else:
            task_results = {}
        rag_result_list = task_results.get("rag", [])
        if "rag" in task_results:
            logger.info(
                f"知识库检索完成: session_id={session_entity.id} "
                f"result_count={len(task_results["rag"])} "
            )

        if rag_result_list:
            rag_section = "以下是与问题相关的知识库内容：\n" + "\n".join(
                "\n".join([rag_result.page_content for rag_result in rag_result_list])
                if rag_result_list
                else ""
            )

        else:
            rag_section = "（本次查询未检索到相关知识库内容，请根据自身专业知识回答）"

        system_prompt = PromptTemplate.from_template(
            get_prompt.chat["CHAT"]["SYSTEM"]
        ).format()
        user_prompt = PromptTemplate.from_template(
            get_prompt.chat["CHAT"]["USER"]
        ).format(
            rag_content_section=rag_section,
            query=chat_request.query,
        )
        history_message_id_list = (session_entity.message_list or [])[
            :-1
        ]  # 去掉最后一条（当前用户消息）
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
        message_list.append(SystemMessage(system_prompt))

        for msg in history_message_list:
            if msg.role == "user":
                message_list.append(HumanMessage(f"用户query:{msg.content}"))
            elif msg.role == "assistant":
                message_list.append(AIMessage(f"ai回复:{msg.content}"))

        message_list.append(HumanMessage(user_prompt))

        yield f"data: {json.dumps({'type': 'progress', 'stage': 'generate', 'message': '正在生成回答...'})}\n\n"

        logger.info(f"LLM 开始生成: session_id={session_entity.id}")

        model = get_model.build_chat_model()
        result = ""
        thinking_parts = []
        async for chunk in model.astream(message_list):
            reasoning = chunk.additional_kwargs.get("reasoning_content")
            if reasoning is not None:
                thinking_parts.append(reasoning)
                yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning}, ensure_ascii=False)}\n\n"

            if not chunk.content:
                continue

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

        new_ids = (session_entity.message_list or []).copy()
        new_ids.append(new_message_entity.id)
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
            models_chat_message.ChatMessage.id.in_(message_id_list),
            models_chat_message.ChatMessage.status == 0,  # 只返回活跃消息
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
    async for chunk in chat(
        user_id,
        schemas_chat.ChatRequest(
            query=re_chat_request.query, session_id=re_chat_request.session_id
        ),
    ):
        yield chunk


async def _identify_intent(query: str):
    """意图识别"""
    system_prompt = PromptTemplate.from_template(
        get_prompt.chat["INTENT"]["SYSTEM"]
    ).format()
    user_prompt = PromptTemplate.from_template(
        get_prompt.chat["INTENT"]["USER"]
    ).format(query=query)
    llm_messages = [SystemMessage(system_prompt), HumanMessage(user_prompt)]

    model = get_model.build_chat_model(thinking=False)
    chain = model | JsonOutputParser()

    try:
        parsed_output: dict = await chain.ainvoke(llm_messages)
        return parsed_output
    except Exception as exc:
        logger.error(f"意图识别错误:{str(exc)}")
        raise ServiceException(ErrorCode.AI_SERVICE_ERROR, "意图识别错误")


async def _rag_retriever(query: str):
    """rag检索"""
    vector_store = get_vector_store()

    tasks = [
        asyncio.to_thread(
            vector_store.similarity_search_with_relevance_scores,
            query=query,
            k=settings.TOP_K,
            filter={"doc_type": doc_type.value},
        )
        for doc_type in schemas_documents.DocumentType
    ]
    results = await asyncio.gather(*tasks)

    for doc_type, sublist in zip(schemas_documents.DocumentType, results):
        logger.info(f"RAG检索各类型数量: doc_type={doc_type.name} count={len(sublist)}")

    fused_results: list[tuple[Document, float]] = []
    for doc_type, doc_scores in zip(schemas_documents.DocumentType, results):
        for doc, score in doc_scores:
            fused_results.append(
                (doc, score * constants_documents.DOCUMENT_WEIGHT[doc_type])
            )

    fused_results.sort(key=lambda x: x[1], reverse=True)

    if fused_results:
        logger.info(
            f"RAG加权融合完成: total={len(fused_results)} "
            f"top1_score={fused_results[0][1]:.4f}"
        )
    top_docs = [doc for doc, score in fused_results[:10]]

    return await _re_sort(query, top_docs)


async def _re_sort(query: str, document_list: list[Document]):
    """重排序"""
    logger.info(f"重排序解析开始: parsed={query} " f"len={len(document_list)}")

    docs_text = ""
    for i, document in enumerate(document_list):
        docs_text += f"文档{i}:{document.page_content}\n"

    system_prompt = PromptTemplate.from_template(
        get_prompt.chat["RESORT"]["SYSTEM"]
    ).format()
    user_prompt = PromptTemplate.from_template(
        get_prompt.chat["RESORT"]["USER"]
    ).format(query=query, doc_count=len(document_list), document_list=docs_text)
    llm_messages = [SystemMessage(system_prompt), HumanMessage(user_prompt)]

    model = get_model.build_chat_model(thinking=False)
    chain = model | JsonOutputParser()

    try:
        parsed_output = await chain.ainvoke(llm_messages)
        ranked_items = [
            schemas_chat.ReSortResultItem.model_validate(r) for r in parsed_output
        ]
    except Exception as e:
        logger.warning(f"重排序失败，退回原始排序: query={query[:50]},e:{str(e)}")
        return document_list[:5]

    logger.info(
        f"重排序解析完成: parsed={len(ranked_items)} "
        f"scores={[r.score for r in ranked_items]}"
    )

    ranked_items.sort(key=lambda x: x.score, reverse=True)

    before_labels = [
        f"{d.metadata.get('doc_id', '?')}-{d.metadata.get('chunk_index', '?')}"
        for d in document_list[:5]
    ]

    seen_indices = set()
    ranked_docs: list[Document] = []
    for item in ranked_items:
        doc_index = item.index
        if 0 <= doc_index < len(document_list) and doc_index not in seen_indices:
            ranked_docs.append(document_list[doc_index])
            seen_indices.add(doc_index)
        if len(ranked_docs) >= 5:
            break

    after_labels = [
        f"{d.metadata.get('doc_id', '?')}-{d.metadata.get('chunk_index', '?')}"
        for d in ranked_docs[:5]
    ]

    logger.info(
        f"重排序完成: before=[{', '.join(before_labels)}] "
        f"after=[{', '.join(after_labels)}]"
    )

    return ranked_docs or document_list[:5]
