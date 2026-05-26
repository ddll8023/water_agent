from fastapi import APIRouter, Depends, Body, Query, Path
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
    dependencies=[Depends(require_role(["admin"]))],
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


@router.post(
    "/add",
    response_model=ApiResponse[schemas_users.AddUserResponse],
    description="添加用户",
    dependencies=[Depends(require_role(["admin"]))],
)
async def add_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    add_user_request: Annotated[
        schemas_users.AddUserRequest, Body(..., description="添加用户请求")
    ],
):
    """添加用户"""
    try:
        return success(await service_users.add_user(db, add_user_request))
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_users.GetUserDetailResponse],
    description="获取用户详情",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_user_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="用户 ID")],
):
    """获取用户详情"""
    try:
        return success(await service_users.get_user_detail(db, id))
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse[schemas_users.UpdateUserResponse],
    description="更新用户",
    dependencies=[Depends(require_role(["admin"]))],
)
async def update_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="用户 ID")],
    update_user_request: Annotated[
        schemas_users.UpdateUserRequest, Body(..., description="更新用户请求")
    ],
):
    """更新用户"""
    try:
        return success(await service_users.update_user(db, id, update_user_request))
    except ServiceException as e:
        return error(e.code, e.message)
