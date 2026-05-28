from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import role as models_role
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.schemas import roles as schemas_roles
import math
from app.models import indicator as models_indicator
from app.schemas import indicators as schemas_indicators
from app.utils.exception import ServiceException


async def create_indicator(
    db: AsyncSession,
    create_indicator_request: schemas_indicators.CreateIndicatorRequest,
):
    """创建指标"""
    indicator_entity = await db.scalar(
        select(models_indicator.Indicator).where(
            models_indicator.Indicator.code == create_indicator_request.code
        )
    )
    if indicator_entity:
        raise ServiceException(ErrorCode.RESOURCE_ALREADY_EXISTS, "指标编码已存在")
    indicator_entity = models_indicator.Indicator(
        **schemas_indicators.CreateIndicatorRequest.model_dump(create_indicator_request)
    )
    db.add(indicator_entity)
    await commit_or_rollback(db)
    return True


async def get_indicator_list(
    db: AsyncSession,
    get_indicator_list_request: schemas_indicators.GetIndicatorListRequest,
):
    """获取指标列表"""
    total = await db.scalar(select(func.count(models_indicator.Indicator.id)))
    stmt = select(models_indicator.Indicator)
    if get_indicator_list_request.name:
        stmt = stmt.where(
            models_indicator.Indicator.name.contains(get_indicator_list_request.name)
        )
    if get_indicator_list_request.code:
        stmt = stmt.where(
            models_indicator.Indicator.code.contains(get_indicator_list_request.code)
        )
    if get_indicator_list_request.category:
        stmt = stmt.where(
            models_indicator.Indicator.category.contains(
                get_indicator_list_request.category
            )
        )
    if get_indicator_list_request.is_core is not None:
        stmt = stmt.where(
            models_indicator.Indicator.is_core == get_indicator_list_request.is_core
        )

    indicator_entitie_list = await db.scalars(
        stmt.order_by(models_indicator.Indicator.id)
        .offset(
            (get_indicator_list_request.page - 1) * get_indicator_list_request.page_size
        )
        .limit(get_indicator_list_request.page_size)
    )
    return PaginatedResponse(
        lists=[
            schemas_indicators.GetIndicatorListResponse.model_validate(indicator_entity)
            for indicator_entity in indicator_entitie_list
        ],
        pagination=PaginationInfo(
            total=total,
            total_pages=math.ceil(total / get_indicator_list_request.page_size),
            page=get_indicator_list_request.page,
            page_size=get_indicator_list_request.page_size,
        ),
    )
