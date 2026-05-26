from fastapi import APIRouter, Depends, Body, Query
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
