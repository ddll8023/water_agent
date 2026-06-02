from fastapi import APIRouter, Depends, Query, Body, Path
from typing import Annotated

from sqlalchemy.sql.schema import Identity
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import monitorings as schemas_monitorings
from app.services import monitoring as services_monitoring
import math

router = APIRouter(prefix="/api/monitoring", tags=["监测数据模块"])


@router.get(
    "/records",
    response_model=ApiResponse[
        PaginatedResponse[schemas_monitorings.GetMonitoringRecordsListResponse]
    ],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取监测记录列表",
)
async def get_monitoring_records_list(
    db: AsyncSession = Depends(get_db),
    get_monitoring_records_list_request: schemas_monitorings.GetMonitoringRecordsListRequest = Query(
        ...
    ),
):
    try:
        result = await services_monitoring.get_monitoring_records_list(
            db, get_monitoring_records_list_request
        )
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/last",
    response_model=ApiResponse[
        schemas_monitorings.GetReservoirLatestIndicatorsResponse
    ],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取水库各指标最新监测值",
)
async def get_reservoir_latest_indicators(
    db: AsyncSession = Depends(get_db),
    request: schemas_monitorings.GetReservoirLatestIndicatorsRequest = Query(
        ..., description="获取水库各指标最新值请求参数"
    ),
):
    try:
        result = await services_monitoring.get_reservoir_latest_indicators(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/trend",
    response_model=ApiResponse[schemas_monitorings.GetMonitoringRecordsTrendResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    summary="获取监测记录趋势",
)
async def get_monitoring_records_trend(
    db: AsyncSession = Depends(get_db),
    get_monitoring_records_trend_request: schemas_monitorings.GetMonitoringRecordsTrendRequest = Query(
        ..., description="获取监测记录趋势请求参数"
    ),
):
    try:
        result = await services_monitoring.get_monitoring_records_trend(
            db, get_monitoring_records_trend_request
        )
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
