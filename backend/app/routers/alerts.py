from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.response import success, error
from app.schemas import alerts as schemas_alerts
from app.services import alerts as services_alerts
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/alerts", tags=["预警模块"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[schemas_alerts.GetAlertListResponse]],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取预警列表",
)
async def get_alert_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[schemas_alerts.GetAlertListRequest, Query()],
):
    """分页查询预警列表，支持按水库、等级、状态、检出时间范围筛选"""
    try:
        result = await services_alerts.get_alert_list(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
