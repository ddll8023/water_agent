from fastapi import APIRouter, Depends, Query, Path, Form, UploadFile, File
from typing import Annotated

from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import require_role
from app.schemas import documents as schemas_documents
from app.services import documents as service_documents

router = APIRouter(prefix="/api/v1/documents", tags=["知识库模块"])


@router.get(
    "",
    response_model=ApiResponse[
        PaginatedResponse[schemas_documents.KnowledgeDocumentItem]
    ],
    dependencies=[Depends(require_role("admin"))],
    description="获取知识库文档列表",
)
async def get_document_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[schemas_documents.GetDocumentListRequest, Depends()],
):
    """获取知识库文档列表"""
    try:
        result = await service_documents.get_document_list(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_documents.KnowledgeDocumentDetail],
    dependencies=[Depends(require_role("admin"))],
    description="获取知识库文档详情",
)
async def get_document_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="文档ID")],
):
    """获取知识库文档详情"""
    try:
        result = await service_documents.get_document_detail(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/upload",
    response_model=ApiResponse[schemas_documents.UploadDocumentResponse],
    dependencies=[Depends(require_role("admin"))],
    summary="上传文档请求",
)
async def upload_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    files: Annotated[
        list[UploadFile],
        File(...),
    ],
    category: Annotated[
        int, Form(..., description="文档类型：0=标准 1=案例 2=预案 3=其他")
    ],
):
    """上传文档请求"""
    try:
        result = await service_documents.upload_document(db, files, category)
        return success(result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除知识库文档（含文件、向量、DB记录）",
)
async def delete_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="文档ID")],
):
    """删除文档"""
    try:
        result = await service_documents.delete_document(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/{id}/reprocess",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    summary="重新处理文档",
)
async def reprocess_document(
    db: Annotated[AsyncSession, Depends(get_db)], id: Annotated[int, Path(...)]
):
    """重新处理文档"""
    try:
        result = await service_documents.reprocess_document(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
