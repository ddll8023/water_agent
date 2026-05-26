from fastapi import APIRouter, Depends, Body, Query, Path
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import roles as schemas_roles
from app.services import roles as service_roles
import math

router = APIRouter(prefix="/api/roles", tags=["角色模块"])


@router.get(
    "/list",
    response_model=ApiResponse[PaginatedResponse[schemas_roles.GetRoleListResponse]],
    description="获取角色列表",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_role_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_role_list_request: Annotated[schemas_roles.GetRoleListRequest, Query()],
):
    """获取角色列表"""
    try:
        return success(await service_roles.get_role_list(db, get_role_list_request))
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/add",
    response_model=ApiResponse[schemas_roles.AddRoleResponse],
    description="添加角色",
    dependencies=[Depends(require_role(["admin"]))],
)
async def add_role(
    db: Annotated[AsyncSession, Depends(get_db)],
    add_role_request: Annotated[
        schemas_roles.AddRoleRequest, Body(..., description="添加角色请求")
    ],
):
    """添加角色"""
    try:
        return success(await service_roles.add_role(db, add_role_request))
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_roles.GetRoleDetailResponse],
    description="获取角色详情",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_role_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="角色 ID")],
):
    """获取角色详情"""
    try:
        return success(await service_roles.get_role_detail(db, id))
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/update",
    response_model=ApiResponse,
    description="更新角色",
    dependencies=[Depends(require_role(["admin"]))],
)
async def update_role(
    db: Annotated[AsyncSession, Depends(get_db)],
    update_role_request: Annotated[
        schemas_roles.UpateRoleRequest, Body(..., description="更新角色请求")
    ],
):
    """更新角色"""
    try:
        return success(await service_roles.update_role(db, update_role_request))
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse,
    description="删除角色",
    dependencies=[Depends(require_role(["admin"]))],
)
async def delete_role(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="角色 ID")],
):
    """删除角色"""
    try:
        return success(await service_roles.delete_role(db, id))
    except ServiceException as e:
        return error(e.code, e.message)
