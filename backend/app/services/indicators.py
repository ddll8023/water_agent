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


async def get_indicator_detail(
    db: AsyncSession,
    indicator_id: int,
):
    """获取指标详情"""
    indicator_entity = await db.get(models_indicator.Indicator, indicator_id)
    if not indicator_entity:
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "指标不存在")
    return schemas_indicators.GetIndicatorDetailResponse.model_validate(
        indicator_entity
    )


async def update_indicator(
    db: AsyncSession,
    indicator_id: int,
    update_indicator_request: schemas_indicators.UpdateIndicatorRequest,
):
    """更新指标"""
    indicator_entity = await db.get(models_indicator.Indicator, indicator_id)
    if not indicator_entity:
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "指标不存在")
    if update_indicator_request.name:
        indicator_entity.name = update_indicator_request.name
    if update_indicator_request.code:
        indicator_entity.code = update_indicator_request.code
    if update_indicator_request.unit:
        indicator_entity.unit = update_indicator_request.unit
    if update_indicator_request.category:
        indicator_entity.category = update_indicator_request.category
    if update_indicator_request.standard_limit_i:
        indicator_entity.standard_limit_i = update_indicator_request.standard_limit_i
    if update_indicator_request.standard_limit_ii:
        indicator_entity.standard_limit_ii = update_indicator_request.standard_limit_ii
    if update_indicator_request.standard_limit_iii:
        indicator_entity.standard_limit_iii = (
            update_indicator_request.standard_limit_iii
        )
    if update_indicator_request.standard_limit_iv:
        indicator_entity.standard_limit_iv = update_indicator_request.standard_limit_iv
    if update_indicator_request.standard_limit_v:
        indicator_entity.standard_limit_v = update_indicator_request.standard_limit_v
    if update_indicator_request.is_core is not None:
        indicator_entity.is_core = update_indicator_request.is_core
    await commit_or_rollback(db)
    return True


async def delete_indicator(
    db: AsyncSession,
    indicator_id: int,
):
    """删除指标"""
    indicator_entity = await db.get(models_indicator.Indicator, indicator_id)
    if not indicator_entity:
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "指标不存在")
    await db.delete(indicator_entity)
    await commit_or_rollback(db)
    return True
