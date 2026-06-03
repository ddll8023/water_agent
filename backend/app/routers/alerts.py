from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role, get_current_user
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.response import success, error
from app.schemas import auth as schemas_auth
from app.schemas import alerts as schemas_alerts
from app.services import alerts as services_alerts
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/alerts", tags=["预警模块"])


@router.get(
    "/unread-count",
    response_model=ApiResponse[schemas_alerts.GetUnreadCountResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取未读预警数",
)
async def get_unread_alert_count(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        result = await services_alerts.get_unread_alert_count(db)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_alerts.GetAlertDetailResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取预警详情",
)
async def get_alert_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: int,
):
    """根据预警ID查询预警详情"""
    try:
        result = await services_alerts.get_alert_detail(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


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


@router.put(
    "/batch-read",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="批量标记已读",
)
async def batch_read_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[
        schemas_alerts.BatchReadAlertsRequest, Body(description="批量已读请求参数")
    ],
):
    try:
        result = await services_alerts.batch_read_alerts(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse[schemas_alerts.GetAlertDetailResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="更新预警状态",
)
async def update_alert(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(description="预警ID")],
    request: Annotated[
        schemas_alerts.UpdateAlertRequest, Body(description="更新预警请求参数")
    ],
):
    """更新预警状态"""
    try:
        result = await services_alerts.update_alert(db, id, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/{id}/notes",
    response_model=ApiResponse[schemas_alerts.AlertNoteResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="添加处置备注",
)
async def add_alert_note(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(description="预警ID")],
    request: Annotated[
        schemas_alerts.AddAlertNoteRequest, Body(description="备注内容")
    ],
    current_user: Annotated[
        schemas_auth.ValidateTokenUserItem, Depends(get_current_user)
    ],
):
    try:
        result = await services_alerts.add_alert_note(
            db, id, current_user.user_id, request
        )
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
