"""指标CRUD服务"""

import asyncio
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, commit_or_rollback, get_background_db_session
from app.core.neo4j import driver
from app.models import indicator as models_indicator
from app.schemas import indicators as schemas_indicators
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)


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
        **create_indicator_request.model_dump()
    )
    db.add(indicator_entity)
    await commit_or_rollback(db)
    asyncio.create_task(
        _sync_indicator_to_neo4j(indicator_entity.id, "create")
    )
    return True


async def get_indicator_list(
    db: AsyncSession,
    get_indicator_list_request: schemas_indicators.GetIndicatorListRequest,
):
    """获取指标列表"""
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

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

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
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "指标不存在")
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
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "指标不存在")
    update_data = update_indicator_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(indicator_entity, key, value)
    await commit_or_rollback(db)
    asyncio.create_task(
        _sync_indicator_to_neo4j(indicator_id, "update")
    )
    return True


async def delete_indicator(
    db: AsyncSession,
    indicator_id: int,
):
    """删除指标"""
    indicator_entity = await db.get(models_indicator.Indicator, indicator_id)
    if not indicator_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "指标不存在")
    code = indicator_entity.code
    await db.delete(indicator_entity)
    await commit_or_rollback(db)
    asyncio.create_task(
        _sync_indicator_to_neo4j(indicator_id, "delete", code)
    )
    return True


"""辅助函数"""


async def _sync_indicator_to_neo4j(indicator_id: int, action: str, entity_code: str | None = None):
    """同步监测指标到 Neo4j"""
    db = None
    neo4j_session = None
    try:
        db = get_background_db_session()
        neo4j_session = driver.session()
        if action == "delete":
            await neo4j_session.run(
                "MATCH (n:Indicator {code: $code}) DETACH DELETE n",
                code=entity_code,
            )
            return

        entity = await db.get(models_indicator.Indicator, indicator_id)
        if not entity:
            return

        await neo4j_session.run(
            """MERGE (i:Indicator {code: $code})
               ON CREATE SET i.name = $name, i.unit = $unit, i.category = $category
               ON MATCH SET i.name = $name, i.unit = $unit, i.category = $category""",
            code=entity.code, name=entity.name,
            unit=entity.unit, category=entity.category,
        )
    except Exception as e:
        logger.error(f"Neo4j 指标同步失败: id={indicator_id}, action={action}, error={e}")
    finally:
        if neo4j_session:
            await neo4j_session.close()
        if db:
            await db.close()
