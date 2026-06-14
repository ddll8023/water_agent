import asyncio
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, commit_or_rollback, get_background_db_session
from app.core.neo4j import driver
from app.models import reservoir as models_reservoir
from app.schemas import reservoir as schemas_reservoir
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)


async def get_reservoir_list(
    db: AsyncSession,
    get_reservoir_list_request: schemas_reservoir.GetReservoirListRequest,
):
    """获取水库列表"""
    stmt = select(models_reservoir.Reservoir)
    if get_reservoir_list_request.keyword:
        stmt = stmt.where(
            models_reservoir.Reservoir.name.ilike(
                f"%{get_reservoir_list_request.keyword}%"
            )
        )
    if get_reservoir_list_request.watershed:
        stmt = stmt.where(
            models_reservoir.Reservoir.watershed == get_reservoir_list_request.watershed
        )
    if get_reservoir_list_request.water_grade:
        stmt = stmt.where(
            models_reservoir.Reservoir.water_grade
            == get_reservoir_list_request.water_grade
        )
    if get_reservoir_list_request.status is not None:
        stmt = stmt.where(
            models_reservoir.Reservoir.status == get_reservoir_list_request.status
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    reservoir_entity_list = await db.scalars(
        stmt.order_by(models_reservoir.Reservoir.id.desc())
        .offset(
            (get_reservoir_list_request.page - 1) * get_reservoir_list_request.page_size
        )
        .limit(get_reservoir_list_request.page_size)
    )

    return PaginatedResponse(
        lists=[
            schemas_reservoir.GetReservoirListResponse.model_validate(reservoir_entity)
            for reservoir_entity in reservoir_entity_list
        ],
        pagination=PaginationInfo(
            total=total or 0,
            total_pages=math.ceil((total or 0) / get_reservoir_list_request.page_size),
            page=get_reservoir_list_request.page,
            page_size=get_reservoir_list_request.page_size,
        ),
    )


async def create_reservoir(
    db: AsyncSession, create_reservoir_request: schemas_reservoir.CreateReservoirRequest
):
    """创建水库"""
    existing = await db.scalar(
        select(models_reservoir.Reservoir).where(
            models_reservoir.Reservoir.code == create_reservoir_request.code
        )
    )
    if existing:
        raise ServiceException(ErrorCode.RESOURCE_ALREADY_EXISTS, "水库已存在")

    reservoir_entity = models_reservoir.Reservoir(
        **create_reservoir_request.model_dump()
    )
    db.add(reservoir_entity)
    await commit_or_rollback(db)
    await db.refresh(reservoir_entity)
    asyncio.create_task(_sync_reservoir_to_neo4j(reservoir_entity.id, "create"))
    return True


async def get_reservoir_detail(db: AsyncSession, reservoir_id: int):
    """获取水库详情"""
    reservoir_entity = await db.get(models_reservoir.Reservoir, reservoir_id)
    if not reservoir_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")
    return schemas_reservoir.GetReservoirDetailResponse.model_validate(reservoir_entity)


async def update_reservoir(
    db: AsyncSession,
    reservoir_id: int,
    update_reservoir_request: schemas_reservoir.UpdateReservoirRequest,
):
    """更新水库"""
    reservoir_entity = await db.get(models_reservoir.Reservoir, reservoir_id)
    if not reservoir_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")
    if (
        update_reservoir_request.code is not None
        and update_reservoir_request.code != reservoir_entity.code
    ):
        existing = await db.scalar(
            select(models_reservoir.Reservoir).where(
                models_reservoir.Reservoir.code == update_reservoir_request.code
            )
        )
        if existing and existing.id != reservoir_id:
            raise ServiceException(ErrorCode.RESOURCE_ALREADY_EXISTS, "水库编码已存在")
        reservoir_entity.code = update_reservoir_request.code
    if update_reservoir_request.name is not None:
        reservoir_entity.name = update_reservoir_request.name
    if update_reservoir_request.location is not None:
        reservoir_entity.location = update_reservoir_request.location
    if update_reservoir_request.longitude is not None:
        reservoir_entity.longitude = update_reservoir_request.longitude
    if update_reservoir_request.latitude is not None:
        reservoir_entity.latitude = update_reservoir_request.latitude
    if update_reservoir_request.capacity is not None:
        reservoir_entity.capacity = update_reservoir_request.capacity
    if update_reservoir_request.watershed is not None:
        reservoir_entity.watershed = update_reservoir_request.watershed
    if update_reservoir_request.water_grade is not None:
        reservoir_entity.water_grade = update_reservoir_request.water_grade
    if update_reservoir_request.status is not None:
        reservoir_entity.status = update_reservoir_request.status
    if update_reservoir_request.sort_order is not None:
        reservoir_entity.sort_order = update_reservoir_request.sort_order

    await commit_or_rollback(db)
    asyncio.create_task(_sync_reservoir_to_neo4j(reservoir_id, "update"))
    return True


async def delete_reservoir(db: AsyncSession, reservoir_id: int):
    """删除水库"""
    reservoir_entity = await db.get(models_reservoir.Reservoir, reservoir_id)
    if not reservoir_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")
    code = reservoir_entity.code
    await db.delete(reservoir_entity)
    await commit_or_rollback(db)
    asyncio.create_task(_sync_reservoir_to_neo4j(reservoir_id, "delete", code))
    return True


"""辅助函数"""


async def _sync_reservoir_to_neo4j(reservoir_id: int, action: str, entity_code: str | None = None):
    """同步水库到 Neo4j"""
    try:
        async with driver.session() as neo4j_session:
            if action == "delete":
                await neo4j_session.run(
                    "MATCH (n:Reservoir {code: $code}) DETACH DELETE n",
                    code=entity_code,
                )
                return

            async with get_background_db_session() as db:
                entity = await db.get(models_reservoir.Reservoir, reservoir_id)
                if not entity:
                    return

                await neo4j_session.run(
                    """MERGE (n:Reservoir {code: $code})
                       ON CREATE SET n.name = $name, n.waterGrade = $waterGrade,
                           n.capacity = $capacity, n.watershed = $watershed,
                           n.longitude = $longitude, n.latitude = $latitude
                       ON MATCH SET n.name = $name, n.waterGrade = $waterGrade,
                           n.capacity = $capacity, n.watershed = $watershed,
                           n.longitude = $longitude, n.latitude = $latitude""",
                    code=entity.code, name=entity.name,
                    waterGrade=entity.water_grade,
                    capacity=entity.capacity,
                    watershed=entity.watershed,
                    longitude=entity.longitude,
                    latitude=entity.latitude,
                )
    except Exception as e:
        logger.error(f"Neo4j 水库同步失败: id={reservoir_id}, action={action}, error={e}")
