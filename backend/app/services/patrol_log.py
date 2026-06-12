"""巡检日志查询服务"""

import math
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patrol_log import PatrolLog
from app.schemas.patrol_log import GetPatrolLogListRequest, GetPatrolLogListResponse
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.core.database import commit_or_rollback


async def get_patrol_log_list(
    db: AsyncSession,
    request: GetPatrolLogListRequest,
) -> PaginatedResponse[GetPatrolLogListResponse]:
    """获取巡检日志列表"""
    stmt = select(PatrolLog)

    if request.status is not None:
        stmt = stmt.where(PatrolLog.status == request.status)
    if request.start_time is not None:
        stmt = stmt.where(PatrolLog.executed_at >= request.start_time)
    if request.end_time is not None:
        stmt = stmt.where(PatrolLog.executed_at <= request.end_time)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    log_entity_list = (
        await db.scalars(
            stmt.order_by(PatrolLog.executed_at.desc())
            .offset((request.page - 1) * request.page_size)
            .limit(request.page_size)
        )
    ).all()

    return PaginatedResponse(
        lists=[
            GetPatrolLogListResponse.model_validate(entity)
            for entity in log_entity_list
        ],
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total or 0,
            total_pages=math.ceil((total or 0) / request.page_size),
        ),
    )


async def delete_patrol_log(db: AsyncSession, log_id: int) -> bool:
    """删除巡检日志"""
    log_entity = await db.get(PatrolLog, log_id)
    if not log_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "日志不存在")

    await db.delete(log_entity)
    await commit_or_rollback(db)
    return True
