import asyncio
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, commit_or_rollback, get_background_db_session
from app.core.neo4j import driver
from app.models import station as models_station
from app.models import reservoir as models_reservoir
from app.models import indicator as models_indicator
from app.schemas import stations as schemas_stations
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)


async def create_monitoring_station(
    db: AsyncSession,
    create_monitoring_station_request: schemas_stations.CreateMonitoringStationRequest,
):
    """创建监测站点"""
    monitoring_station_entity = await db.scalar(
        select(models_station.MonitoringStation).where(
            models_station.MonitoringStation.code
            == create_monitoring_station_request.code
        )
    )
    if monitoring_station_entity:
        raise ServiceException(ErrorCode.RESOURCE_ALREADY_EXISTS, "监测站点已存在")
    monitoring_station_entity = models_station.MonitoringStation(
        **schemas_stations.CreateMonitoringStationRequest.model_dump(
            create_monitoring_station_request
        )
    )
    db.add(monitoring_station_entity)
    await commit_or_rollback(db)
    asyncio.create_task(_sync_station_to_neo4j(monitoring_station_entity.id, "create"))
    return True


async def get_monitoring_station_list(
    db: AsyncSession,
    get_monitoring_station_list_request: schemas_stations.GetMonitoringStationListRequest,
):
    """获取监测站点列表"""

    stmt = select(models_station.MonitoringStation)
    if get_monitoring_station_list_request.reservoir_id is not None:
        stmt = stmt.where(
            models_station.MonitoringStation.reservoir_id
            == get_monitoring_station_list_request.reservoir_id
        )
    if get_monitoring_station_list_request.keyword is not None:
        stmt = stmt.where(
            models_station.MonitoringStation.name.contains(
                get_monitoring_station_list_request.keyword
            )
        )
    if get_monitoring_station_list_request.code is not None:
        stmt = stmt.where(
            models_station.MonitoringStation.code.contains(
                get_monitoring_station_list_request.code
            )
        )
    if get_monitoring_station_list_request.type is not None:
        stmt = stmt.where(
            models_station.MonitoringStation.type
            == get_monitoring_station_list_request.type
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    monitoring_station_entities_list = await db.scalars(
        stmt.order_by(models_station.MonitoringStation.id.desc())
        .offset(
            (get_monitoring_station_list_request.page - 1)
            * get_monitoring_station_list_request.page_size
        )
        .limit(get_monitoring_station_list_request.page_size)
    )
    return PaginatedResponse(
        lists=[
            schemas_stations.GetMonitoringStationListResponse.model_validate(
                monitoring_station_entity
            )
            for monitoring_station_entity in monitoring_station_entities_list
        ],
        pagination_info=PaginationInfo(
            total=total,
            total_pages=math.ceil(
                total / get_monitoring_station_list_request.page_size
            ),
            page=get_monitoring_station_list_request.page,
            page_size=get_monitoring_station_list_request.page_size,
        ),
    )


async def get_monitoring_station_detail(
    db: AsyncSession,
    monitoring_station_id: int,
):
    """获取监测站点详情"""
    monitoring_station_entity = await db.get(
        models_station.MonitoringStation, monitoring_station_id
    )
    if not monitoring_station_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")
    return schemas_stations.GetMonitoringStationDetailResponse.model_validate(
        monitoring_station_entity
    )


async def update_monitoring_station(
    db: AsyncSession,
    monitoring_station_id: int,
    update_monitoring_station_request: schemas_stations.UpdateMonitoringStationRequest,
):
    """更新监测站点"""
    monitoring_station_entity = await db.get(
        models_station.MonitoringStation, monitoring_station_id
    )
    if not monitoring_station_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")
    if update_monitoring_station_request.name is not None:
        monitoring_station_entity.name = update_monitoring_station_request.name
    if (
        update_monitoring_station_request.code is not None
        and update_monitoring_station_request.code != monitoring_station_entity.code
    ):
        existing_code = await db.scalar(
            select(models_station.MonitoringStation).where(
                models_station.MonitoringStation.code
                != update_monitoring_station_request.code
            )
        )
        if existing_code is not None:
            raise ServiceException(
                ErrorCode.RESOURCE_ALREADY_EXISTS, "监测站点编码已存在"
            )
        monitoring_station_entity.code = update_monitoring_station_request.code
    if update_monitoring_station_request.type is not None:
        monitoring_station_entity.type = update_monitoring_station_request.type
    if update_monitoring_station_request.reservoir_id is not None:
        monitoring_station_entity.reservoir_id = (
            update_monitoring_station_request.reservoir_id
        )
    if update_monitoring_station_request.sampling_point is not None:
        monitoring_station_entity.sampling_point = (
            update_monitoring_station_request.sampling_point
        )
    if update_monitoring_station_request.status is not None:
        monitoring_station_entity.status = update_monitoring_station_request.status
    if update_monitoring_station_request.longitude is not None:
        monitoring_station_entity.longitude = (
            update_monitoring_station_request.longitude
        )
    if update_monitoring_station_request.latitude is not None:
        monitoring_station_entity.latitude = update_monitoring_station_request.latitude
    await commit_or_rollback(db)
    asyncio.create_task(_sync_station_to_neo4j(monitoring_station_id, "update"))
    return True


async def delete_monitoring_station(
    db: AsyncSession,
    monitoring_station_id: int,
):
    """删除监测站点"""
    monitoring_station_entity = await db.get(
        models_station.MonitoringStation, monitoring_station_id
    )
    if not monitoring_station_entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")
    code = monitoring_station_entity.code
    await db.delete(monitoring_station_entity)
    await commit_or_rollback(db)
    asyncio.create_task(_sync_station_to_neo4j(monitoring_station_id, "delete", code))
    return True


"""辅助函数"""


async def _sync_station_to_neo4j(station_id: int, action: str, entity_code: str | None = None):
    """同步监测站点到 Neo4j（含 BELONGS_TO + MEASURES）"""
    try:
        async with driver.session() as neo4j_session:
            if action == "delete":
                await neo4j_session.run(
                    "MATCH (n:MonitoringStation {code: $code}) DETACH DELETE n",
                    code=entity_code,
                )
                return

            async with get_background_db_session() as db:
                entity = await db.get(models_station.MonitoringStation, station_id)
                if not entity:
                    return

                await neo4j_session.run(
                    """MERGE (s:MonitoringStation {code: $code})
                       ON CREATE SET s.name = $name, s.type = $type,
                           s.longitude = $longitude, s.latitude = $latitude,
                           s.samplingPoint = $samplingPoint
                       ON MATCH SET s.name = $name, s.type = $type,
                           s.longitude = $longitude, s.latitude = $latitude,
                           s.samplingPoint = $samplingPoint""",
                    code=entity.code, name=entity.name, type=entity.type,
                    longitude=entity.longitude,
                    latitude=entity.latitude,
                    samplingPoint=entity.sampling_point,
                )

                reservoir = await db.get(models_reservoir.Reservoir, entity.reservoir_id)
                if reservoir:
                    await neo4j_session.run(
                        """MATCH (s:MonitoringStation {code: $scode})
                           MATCH (r:Reservoir {code: $rcode})
                           MERGE (s)-[:BELONGS_TO]->(r)""",
                        scode=entity.code, rcode=reservoir.code,
                    )

                indicators = (await db.execute(select(models_indicator.Indicator))).scalars().all()
                for ind in indicators:
                    await neo4j_session.run(
                        """MATCH (s:MonitoringStation {code: $scode})
                           MATCH (i:Indicator {code: $icode})
                           MERGE (s)-[:MEASURES]->(i)""",
                        scode=entity.code, icode=ind.code,
                    )
    except Exception as e:
        logger.error(f"Neo4j 站点同步失败: id={station_id}, action={action}, error={e}")
