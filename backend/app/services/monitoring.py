"""监测数据模拟服务"""

from datetime import datetime

from app.utils.exception import ServiceException
from app.schemas.common import ErrorCode
from app.schemas import monitorings as schemas_monitorings
from app.utils.mock_data_generator import RTU_STATION_CONFIG, generate_rtu_indicators


async def mock_monitoring_record(
    get_mock_monitoring_record: schemas_monitorings.GetMockMonitoringRecordRequest,
):
    """模拟自动站 RTU 数据"""
    station_id = get_mock_monitoring_record.station_id
    station_config = RTU_STATION_CONFIG.get(station_id)
    if not station_config:
        raise ServiceException(
            ErrorCode.DATA_NOT_FOUND, f"未找到站点配置: station_id={station_id}"
        )

    if station_config.get("offline"):
        raise ServiceException(
            ErrorCode.DATA_NOT_FOUND, f"站点离线: {station_config['code']}"
        )

    raw_indicators = generate_rtu_indicators(station_config["water_grade"])
    indicators = [
        schemas_monitorings.MockRtuIndicatorItem(
            indicator_code=code,
            indicator_name=name,
            value=value,
            unit=unit,
        )
        for code, name, value, unit in raw_indicators
    ]
    return schemas_monitorings.MockRtuDataResponse(
        station_id=station_id,
        station_code=station_config["code"],
        reservoir_id=station_config["reservoir_id"],
        reservoir_name=station_config["reservoir_name"],
        record_time=datetime.now(),
        indicators=indicators,
        water_grade=station_config["water_grade"],
    )
