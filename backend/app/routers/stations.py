from fastapi import APIRouter, Depends, Query, Body, Path
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import stations as schemas_stations
from app.services import stations as service_stations

router = APIRouter(prefix="/api/stations", tags=["监测站模块"])


@router.post(
    "/create",
    response_model=ApiResponse[bool],
    description="创建监测站点",
    dependencies=[Depends(require_role(["admin"]))],
)
async def create_monitoring_station(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_monitoring_station_request: Annotated[
        schemas_stations.CreateMonitoringStationRequest,
        Body(..., description="创建监测站点请求参数"),
    ],
):
    """创建监测站点"""
    try:
        return success(
            await service_stations.create_monitoring_station(
                db, create_monitoring_station_request
            )
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/list",
    description="获取监测站点列表",
    dependencies=[Depends(require_role(["admin"]))],
)
async def get_monitoring_station_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_monitoring_station_list_request: Annotated[
        schemas_stations.GetMonitoringStationListRequest,
        Query(..., description="获取监测站点列表请求参数"),
    ],
):
    """获取监测站点列表"""
    try:
        return success(
            await service_stations.get_monitoring_station_list(
                db, get_monitoring_station_list_request
            )
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_stations.GetMonitoringStationDetailResponse],
    dependencies=[Depends(require_role(["admin"]))],
    description="获取监测站点详情",
)
async def get_monitoring_station_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="监测站点ID")],
):
    """获取监测站点详情"""
    try:
        return success(await service_stations.get_monitoring_station_detail(db, id))
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse[bool],
    description="更新监测站点",
    dependencies=[Depends(require_role(["admin"]))],
)
async def update_monitoring_station(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="监测站点ID")],
    update_monitoring_station_request: Annotated[
        schemas_stations.UpdateMonitoringStationRequest,
        Body(..., description="更新监测站点请求参数"),
    ],
):
    """更新监测站点"""
    try:
        return success(
            await service_stations.update_monitoring_station(
                db, id, update_monitoring_station_request
            )
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    description="删除监测站点",
    dependencies=[Depends(require_role(["admin"]))],
)
async def delete_monitoring_station(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="监测站点ID")],
):
    """删除监测站点"""
    try:
        return success(await service_stations.delete_monitoring_station(db, id))
    except ServiceException as e:
        return error(e.code, e.message)
