from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.neo4j import get_neo4j_session
from app.core.security import require_role, get_current_user
from app.schemas.common import ApiResponse, PaginatedResponse
from neo4j import AsyncDriver
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
    "/{id}/trace",
    response_model=ApiResponse[schemas_alerts.GetTracePollutionResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取预警溯源路径",
)
async def get_alert_trace(
    db: Annotated[AsyncSession, Depends(get_db)],
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    id: int,
):
    """获取预警溯源路径"""
    try:
        result = await services_alerts.get_alert_trace(db, neo4j_driver, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/{id}/similar",
    response_model=ApiResponse[PaginatedResponse[schemas_alerts.SimilarEventItem]],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取历史相似事件",
)
async def get_similar_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """按同水库+指标匹配数排序，返回已解决的历史预警"""
    try:
        result = await services_alerts.get_similar_events(db, id, page, page_size)
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


@router.post(
    "/{id}/suggestion",
    response_model=ApiResponse[schemas_alerts.LLMSuggestionResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="生成AI处置建议",
)
async def llm_suggestion(
    db: Annotated[AsyncSession, Depends(get_db)],
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    id: Annotated[int, Path(description="预警ID")],
):
    """生成ai建议"""
    try:
        result = await services_alerts.llm_suggestion(db, neo4j_driver, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
