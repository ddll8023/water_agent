import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import alert as models_alert
from app.schemas import alerts as schemas_alerts
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.models import user as models_user
from app.core.database import commit_or_rollback


async def get_alert_detail(
    db: AsyncSession,
    alert_id: int,
):
    """获取预警详情"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)

    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    return schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)


async def get_alert_list(
    db: AsyncSession,
    request: schemas_alerts.GetAlertListRequest,
):
    """获取预警列表"""
    total = await db.scalar(select(func.count(models_alert.AlertEvent.id)))

    stmt = select(models_alert.AlertEvent, models_user.User.real_name).outerjoin(
        models_user.User, models_alert.AlertEvent.handler_id == models_user.User.id
    )
    if request.reservoir_id is not None:
        stmt = stmt.where(models_alert.AlertEvent.reservoir_id == request.reservoir_id)
    if request.alert_level is not None:
        stmt = stmt.where(models_alert.AlertEvent.alert_level == request.alert_level)
    if request.status is not None:
        stmt = stmt.where(models_alert.AlertEvent.status == request.status)
    if request.start_time is not None:
        stmt = stmt.where(models_alert.AlertEvent.detected_at >= request.start_time)
    if request.end_time is not None:
        stmt = stmt.where(models_alert.AlertEvent.detected_at <= request.end_time)

    alert_entity_list = (
        await db.execute(
            stmt.order_by(models_alert.AlertEvent.detected_at.desc())
            .offset((request.page - 1) * request.page_size)
            .limit(request.page_size)
        )
    ).all()

    result_list: list[schemas_alerts.GetAlertListResponse] = []
    for alert_event, handler_name in alert_entity_list:
        resp = schemas_alerts.GetAlertListResponse.model_validate(alert_event)
        resp.handler_name = handler_name
        result_list.append(resp)

    return PaginatedResponse(
        lists=result_list,
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total,
            total_pages=math.ceil(total / request.page_size),
        ),
    )


async def update_alert(
    db: AsyncSession,
    alert_id: int,
    update_alert_request: schemas_alerts.UpdateAlertRequest,
):
    """更新预警状态"""
    alert_entity = await db.get(models_alert.AlertEvent, alert_id)

    if not alert_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "预警记录不存在")

    alert_entity.status = update_alert_request.status
    alert_entity.handler_id = update_alert_request.handler_id

    await commit_or_rollback(db)
    return schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)
