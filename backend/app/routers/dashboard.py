from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.common import ApiResponse
from app.schemas.response import success, error
from app.schemas import dashboard as schemas_dashboard
from app.services import dashboard as services_dashboard
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘模块"])


@router.get(
    "/overview",
    response_model=ApiResponse[schemas_dashboard.GetDashboardOverviewResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取仪表盘总览",
)
async def get_dashboard_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取仪表盘总览"""
    try:
        result = await services_dashboard.get_dashboard_overview(db)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/reservoir-cards",
    response_model=ApiResponse[list[schemas_dashboard.ReservoirCardResponse]],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取水库卡片列表",
)
async def get_reservoir_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取水库卡片列表"""
    try:
        result = await services_dashboard.get_reservoir_cards(db)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/last-alert",
    response_model=ApiResponse[list[schemas_dashboard.GetLastAlertResponse]],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取最近5条告警记录",
)
async def get_last_alert(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取最近5条告警记录"""
    try:
        result = await services_dashboard.get_last_alert(db)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
