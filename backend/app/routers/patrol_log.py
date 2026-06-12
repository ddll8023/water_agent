from typing import Annotated
from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.response import success, error
from app.schemas import patrol_log as schemas_patrol_log
from app.services import patrol_log as services_patrol_log
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/patrol-logs", tags=["巡检日志"])


@router.post(
    "/list",
    response_model=ApiResponse[PaginatedResponse[schemas_patrol_log.GetPatrolLogListResponse]],
    dependencies=[Depends(require_role("admin", "user"))],
    description="获取巡检日志列表",
)
async def get_patrol_log_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[
        schemas_patrol_log.GetPatrolLogListRequest,
        Body(..., description="获取巡检日志列表请求"),
    ],
):
    """获取巡检日志列表"""
    try:
        result = await services_patrol_log.get_patrol_log_list(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除巡检日志",
)
async def delete_patrol_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="日志ID")],
):
    """删除巡检日志"""
    try:
        result = await services_patrol_log.delete_patrol_log(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
