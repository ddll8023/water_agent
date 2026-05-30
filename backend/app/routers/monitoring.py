"""监测数据模拟与采集路由"""

from fastapi import APIRouter, Query
from typing import Annotated
from app.schemas.response import success, error
from app.schemas.common import ApiResponse
from app.utils.exception import ServiceException
from app.schemas import monitorings as schemas_monitorings
from app.services import monitoring as service_monitoring

router = APIRouter(prefix="/api/monitoring", tags=["监测数据"])


@router.get(
    "/simulate",
    response_model=ApiResponse[schemas_monitorings.MockRtuDataResponse],
    summary="模拟自动站 RTU 数据",
)
async def get_mock_monitoring_data(
    station_id: Annotated[int, Query(..., description="站点ID")],
):
    """模拟自动站 RTU 数据"""
    try:
        result = await service_monitoring.mock_monitoring_record(
            schemas_monitorings.GetMockMonitoringRecordRequest(station_id=station_id)
        )
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
