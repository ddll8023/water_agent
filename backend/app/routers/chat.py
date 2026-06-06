"""聊天对话路由（SSE 流式）"""

from fastapi import APIRouter, Depends, Query, Path, Form, UploadFile, File
from typing import Annotated
from fastapi.responses import StreamingResponse
from app.core.security import require_role
from app.core.security import get_current_user
from app.schemas import auth as schemas_auth
from app.schemas import chat as schemas_chat
from app.services import chat as service_chat
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/chat", tags=["智能问答"])


@router.post(
    "", dependencies=[Depends(require_role("admin", "user"))], summary="流式对话"
)
async def chat_stream(
    chat_request: schemas_chat.ChatRequest,
    current_user: Annotated[
        schemas_auth.ValidateTokenUserItem, Depends(get_current_user)
    ],
):
    """SSE 流式对话"""
    return StreamingResponse(
        service_chat.chat(current_user.user_id, chat_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取对话列表请求",
)
async def get_chat_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_chat_list_request: Annotated[schemas_chat.GetChatListRequest, Query()],
):
    """获取对话列表请求"""
    try:
        result = await service_chat.get_chat_list(db, get_chat_list_request)
        return success(result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_chat.GetChatDetailResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取对话详情请求",
)
async def get_chat_detail(
    db: Annotated[AsyncSession, Depends(get_db)], id: Annotated[int, Path()]
):
    """获取对话详情请求"""
    try:
        result = await service_chat.get_chat_detail(db, id)
        return success(result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="删除对话请求",
)
async def delete_chat(
    db: Annotated[AsyncSession, Depends(get_db)], id: Annotated[int, Path()]
):
    """删除对话请求"""

    try:
        result = await service_chat.delete_chat(db, id)
        return success(result)
    except ServiceException as e:
        return error(e.code, e.message)
