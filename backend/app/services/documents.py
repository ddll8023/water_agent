import json
import math
import random
import httpx
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.core.database import commit_or_rollback, get_background_db_session
from app.utils.logger_config import setup_logger
from app.schemas.common import PaginationInfo, PaginatedResponse, ErrorCode
from app.utils.exception import ServiceException
from app.schemas import documents as schemas_documents
from app.models import knowledge_document as models_document
from app.constants import documents as constants_documents
import os
import uuid
import aiofiles
from app.utils.file import save_file, ROOT_DIR
from app.core.config import settings
import asyncio
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from app.core.chroma import get_vector_store
from app.utils.retriever import invalidate_retriever

logger = setup_logger(__name__)

_process_semaphore = asyncio.Semaphore(1)


async def upload_document(
    db: AsyncSession,
    files: list[UploadFile],
    category: int,
):
    """上传文档请求"""
    logger.info(f"收到上传请求: {len(files)} 个文件, category={category}")
    result_list: list[schemas_documents.UploadDocumentItem] = []
    fail_count = 0
    pending_doc_ids: list[int] = []
    for file in files:
        try:
            # 检验
            is_valid, message = await _validate_file(file)
            if not is_valid:
                logger.warning(f"文件校验失败: {file.filename}, {message}")
                raise ServiceException(ErrorCode.INVALID_FILE, message)

            # 保存文件，数据库记录
            filename_list = os.path.splitext(file.filename)
            new_filename = f"{filename_list[0]}_{uuid.uuid4().hex}{filename_list[1]}"
            file_bytes = await file.read()
            await save_file(
                file_bytes,
                os.path.join(ROOT_DIR, settings.UPDATE_PATH_NAME, new_filename),
            )

            document_entity = models_document.KnowledgeDocument(
                title=filename_list[0],
                doc_type=category,
                file_name=filename_list[0],
                file_path=new_filename,
                file_size=file.size,
            )
            db.add(document_entity)
            await db.flush()

            pending_doc_ids.append(document_entity.id)

            result_list.append(
                schemas_documents.UploadDocumentItem(
                    document_id=document_entity.id,
                    file_name=file.filename,
                    file_size=file.size,
                    status=1,
                )
            )

        except Exception as e:
            logger.error(f"文件上传异常: {file.filename}, {e}", exc_info=True)
            result_list.append(
                schemas_documents.UploadDocumentItem(
                    document_id=0,
                    file_name=file.filename,
                    file_size=file.size,
                    status=0,
                    error=str(e),
                )
            )
            fail_count += 1

    await commit_or_rollback(db)

    for doc_id in pending_doc_ids:
        asyncio.create_task(_process_document(document_id=doc_id))

    return schemas_documents.UploadDocumentResponse(
        total=len(files),
        success_count=len(files) - fail_count,
        failed_count=fail_count,
        lists=result_list,
    )


async def get_document_list(
    db: AsyncSession,
    request: schemas_documents.GetDocumentListRequest,
):
    """获取知识库文档列表"""
    base_stmt = select(models_document.KnowledgeDocument)

    if request.keyword:
        base_stmt = base_stmt.where(
            models_document.KnowledgeDocument.file_name.like(f"%{request.keyword}%")
        )
    if request.doc_type is not None:
        base_stmt = base_stmt.where(
            models_document.KnowledgeDocument.doc_type == request.doc_type
        )
    if request.status is not None:
        base_stmt = base_stmt.where(
            models_document.KnowledgeDocument.status == request.status
        )

    total = await db.scalar(select(func.count()).select_from(base_stmt.subquery()))

    items = (
        await db.scalars(
            base_stmt.order_by(models_document.KnowledgeDocument.created_at.desc())
            .offset((request.page - 1) * request.page_size)
            .limit(request.page_size)
        )
    ).all()

    return PaginatedResponse(
        lists=[
            schemas_documents.KnowledgeDocumentItem.model_validate(item)
            for item in items
        ],
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total or 0,
            total_pages=math.ceil((total or 0) / request.page_size),
        ),
    )


async def get_document_detail(db: AsyncSession, document_id: int):
    """获取文档详情"""
    entity = await db.get(models_document.KnowledgeDocument, document_id)
    if not entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "文档不存在")
    return schemas_documents.KnowledgeDocumentDetail.model_validate(entity)


async def delete_document(db: AsyncSession, document_id: int):
    """删除文档"""
    entity = await db.get(models_document.KnowledgeDocument, document_id)
    if not entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "文档不存在")

    file_path = os.path.join(ROOT_DIR, settings.UPDATE_PATH_NAME, entity.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    vector_store = get_vector_store()
    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                vector_store._collection.delete, where={"doc_id": document_id}
            ),
            timeout=30,
        )
    except Exception as e:
        raise ServiceException(message="chroma删除错误")

    invalidate_retriever()
    await db.delete(entity)
    await commit_or_rollback(db)
    logger.info(f"文档已删除: doc_id={document_id}")
    return True


async def reprocess_document(db: AsyncSession, document_id: int):
    """重新处理文档"""
    document_entity = await db.get(models_document.KnowledgeDocument, document_id)
    if not document_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "文档不存在")
    document_entity.status = 1
    document_entity.content = None
    document_entity.chunk_count = 0
    document_entity.error = None
    vector_store = get_vector_store()
    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                vector_store._collection.delete, where={"doc_id": document_id}
            ),
            timeout=30,
        )
    except Exception as e:
        raise ServiceException(message="chroma删除错误")
    await commit_or_rollback(db)
    asyncio.create_task(_process_document(document_entity.id))
    return True


async def _validate_file(file: UploadFile):
    """校验文件"""
    filename = file.filename
    if not filename.endswith(constants_documents.FILE_EXTENSION):
        return False, "仅支持PDF和md格式的文件"
    if file.size > constants_documents.MAX_FILE_SIZE:
        return False, "文件大小不能超过10MB"
    return True, "文件校验通过"


async def _process_document(document_id: int):
    """处理文档"""
    async with _process_semaphore:
        logger.info(f"开始处理文档: doc_id={document_id}")
        db = get_background_db_session()
        document_entity = await db.get(models_document.KnowledgeDocument, document_id)
        if not document_entity:
            logger.warning(f"文档不存在: doc_id={document_id}")
            raise ServiceException(ErrorCode.DATA_NOT_FOUND, "文档不存在")
        try:
            file_text = await _extract_text(document_entity.file_path)
            logger.info(
                f"文档文本提取完成: doc_id={document_id}, 长度={len(file_text)}"
            )
            document_entity.content = file_text
            # 切块
            if document_entity.file_path.endswith("md"):
                splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=[("#", "title"), ("##", "section")]
                )
                doc_chunks = splitter.split_text(file_text)
                splited_text_list = [doc.page_content for doc in doc_chunks]
                metadatas_base = [doc.metadata for doc in doc_chunks]
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                    separators=settings.SEPARATORS,
                    length_function=len,
                )
                splited_text_list = splitter.split_text(file_text)
                metadatas_base = [{} for _ in splited_text_list]

            logger.info(
                f"文档切片完成: doc_id={document_id}, 切片数={len(splited_text_list)}"
            )
            # 向量化
            vector_store = get_vector_store()
            metadatas = []
            for i, base_meta in enumerate(metadatas_base):
                base_meta.update(
                    {
                        "doc_id": document_id,
                        "chunk_index": i,
                        "doc_type": document_entity.doc_type,
                    }
                )
                metadatas.append(base_meta)
            chunk_ids_list = await asyncio.wait_for(
                asyncio.to_thread(
                    vector_store.add_texts,
                    texts=splited_text_list,
                    metadatas=metadatas,
                ),
                timeout=120,
            )
            logger.info(
                f"Chroma 入库完成: doc_id={document_id}, 切片数={len(chunk_ids_list)}"
            )
            document_entity.chunk_count = len(chunk_ids_list)
            document_entity.status = 2
            await commit_or_rollback(db)
            logger.info(f"文档处理完成: doc_id={document_id}")
        except Exception as e:
            logger.error(f"文档处理失败: doc_id={document_id}, {e}", exc_info=True)
            vector_store._collection.delete(where={"doc_id": document_id})
            db.rollback()
            document_entity.status = 3
            document_entity.error = str(e)
            await commit_or_rollback(db)
        finally:
            invalidate_retriever()
            await db.close()


async def _extract_text(filename: str):
    """从文档中提取文本"""
    path = os.path.join(ROOT_DIR, settings.UPDATE_PATH_NAME, filename)
    if not os.path.exists(path):
        logger.error(f"文件不存在: {path}")
        raise ServiceException(message="文件不存在")

    if filename.endswith("pdf"):

        def _read_pdf():
            loader = PyPDFLoader(path)
            content = ""
            for document in loader.load():
                content += document.page_content
            return content

        return await asyncio.to_thread(_read_pdf)
    else:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
