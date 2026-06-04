from fastapi import APIRouter, Depends, Query, Form, UploadFile, File
from typing import Annotated

from sqlalchemy.sql.schema import Identity
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import documents as schemas_documents
from app.services import documents as service_documents
import math

router = APIRouter(prefix="/api/v1/documents", tags=["知识库模块"])


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
    category: Annotated[int, Form(..., description="文档类型：0=标准 1=案例 2=预案 3=其他")],
):
    """上传文档请求"""
    try:
        result = await service_documents.upload_document(db, files, category)
        return success(result)
    except Exception as e:
        return error(e.code, e.message)
