from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import role as models_role
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.schemas import roles as schemas_roles
import math
from app.models import station as models_station
from app.schemas import stations as schemas_stations
from app.utils.exception import ServiceException


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
    return True


async def get_monitoring_station_list(
    db: AsyncSession,
    get_monitoring_station_list_request: schemas_stations.GetMonitoringStationListRequest,
):
    """获取监测站点列表"""
    total = await db.scalar(select(func.count(models_station.MonitoringStation.id)))

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
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "监测站点不存在")
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
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "监测站点不存在")
    if update_monitoring_station_request.name is not None:
        monitoring_station_entity.name = update_monitoring_station_request.name
    if update_monitoring_station_request.code is not None:
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
        raise ServiceException(ErrorCode.RESOURCE_NOT_FOUND, "监测站点不存在")
    await db.delete(monitoring_station_entity)
    await commit_or_rollback(db)
    return True
