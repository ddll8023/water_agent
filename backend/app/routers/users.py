from fastapi import APIRouter, Depends, Body, Query
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException
from app.schemas import users as schemas_users
from app.services import users as service_users
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/users", tags=["用户模块"])


@router.get(
    "/list",
    response_model=ApiResponse[PaginatedResponse[schemas_users.GetUserListResponse]],
    description="获取用户列表",
    dependencies=[Depends(require_role("admin"))],
)
async def get_user_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user_list_request: Annotated[
        schemas_users.GetUserListRequest, Query(..., description="用户列表请求")
    ],
):
    """获取用户列表"""
    try:
        return success(await service_users.get_user_list(db, get_user_list_request))
    except ServiceException as e:
        return error(e.code, e.message)
