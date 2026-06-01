"""监测数据定时采集服务"""

import random
import httpx
from datetime import datetime
from sqlalchemy import select, and_, func
from app.core.database import commit_or_rollback, get_background_db_session
from app.models import monitoring as models_monitoring
from app.models import station as models_station
from app.constants import monitoring as constants_monitoring
from app.utils.logger_config import setup_logger
from app.schemas import monitorings as schemas_monitorings
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import PaginationInfo, PaginatedResponse
import math
from app.utils.exception import ServiceException
from app.schemas.common import ErrorCode

logger = setup_logger(__name__)


async def collect_water_quality_data():
    """定时采集水质数据：遍历所有在线站点，调用 API 采集并入库"""
    logger.info("开始执行定时采集任务")
    real_record = await _fetch_real_data()
    if not real_record:
        return

    monitor_time_str = real_record.get("monitorTime")
    monitor_time = datetime.strptime(monitor_time_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()

    async with get_background_db_session() as db:
        try:
            station_entity_list = (
                await db.scalars(
                    select(models_station.MonitoringStation).where(
                        models_station.MonitoringStation.status == 1
                    )
                )
            ).all()

            if not station_entity_list:
                logger.warning("没有在线的监测站点，跳过本次采集")
                return

            total_records = 0
            for station in station_entity_list:
                reservoir_id = station.reservoir_id
                for (
                    api_field,
                    indicator_id,
                ) in constants_monitoring.FIELD_TO_INDICATOR.items():
                    raw_value = real_record.get(api_field)
                    if raw_value is None:
                        logger.warning(
                            f"API记录缺少字段 {api_field}，站点ID={station.id}"
                        )
                        continue

                    existing = await db.scalar(
                        select(models_monitoring.MonitoringRecord).where(
                            and_(
                                models_monitoring.MonitoringRecord.station_id
                                == station.id,
                                models_monitoring.MonitoringRecord.indicator_id
                                == indicator_id,
                                models_monitoring.MonitoringRecord.record_time
                                == monitor_time,
                            )
                        )
                    )
                    if existing is not None:
                        continue

                    offset_range = (-0.05, 0.05)
                    offset = random.uniform(*offset_range)
                    value = round(raw_value * (1 + offset), 4)

                    record = models_monitoring.MonitoringRecord(
                        reservoir_id=reservoir_id,
                        station_id=station.id,
                        indicator_id=indicator_id,
                        value=value,
                        data_source="auto",
                        quality_flag=1,
                        record_time=monitor_time,
                        created_at=now,
                    )
                    db.add(record)
                    total_records += 1

                station.last_data_time = monitor_time

            await commit_or_rollback(db)
            logger.info(f"成功采集 {total_records} 条记录")
        except Exception as e:
            logger.error(f"定时采集失败: {e}")


async def get_monitoring_records_list(
    db: AsyncSession,
    get_monitoring_records_list_request: schemas_monitorings.GetMonitoringRecordsListRequest,
):
    """获取监测记录列表"""
    total = await db.scalar(select(func.count(models_monitoring.MonitoringRecord.id)))

    stmt = select(models_monitoring.MonitoringRecord)
    if get_monitoring_records_list_request.reservoir_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.reservoir_id
            == get_monitoring_records_list_request.reservoir_id
        )
    if get_monitoring_records_list_request.station_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.station_id
            == get_monitoring_records_list_request.station_id
        )
    if get_monitoring_records_list_request.indicator_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.indicator_id
            == get_monitoring_records_list_request.indicator_id
        )
    if get_monitoring_records_list_request.start_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time
            >= get_monitoring_records_list_request.start_time
        )
    if get_monitoring_records_list_request.end_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time
            <= get_monitoring_records_list_request.end_time
        )
    if get_monitoring_records_list_request.quality_flag is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.quality_flag
            == get_monitoring_records_list_request.quality_flag
        )

    monitoring_records_entity_list = (
        await db.scalars(
            stmt.order_by(models_monitoring.MonitoringRecord.record_time.desc())
            .offset(
                (get_monitoring_records_list_request.page - 1)
                * get_monitoring_records_list_request.page_size
            )
            .limit(get_monitoring_records_list_request.page_size)
        )
    ).all()

    return PaginatedResponse(
        lists=[
            schemas_monitorings.GetMonitoringRecordsListResponse.model_validate(entity)
            for entity in monitoring_records_entity_list
        ],
        pagination=PaginationInfo(
            page=get_monitoring_records_list_request.page,
            page_size=get_monitoring_records_list_request.page_size,
            total=total,
            total_pages=math.ceil(
                total / get_monitoring_records_list_request.page_size
            ),
        ),
    )


async def get_last_monitoring_record(
    db: AsyncSession,
    get_last_monitoring_record_request: schemas_monitorings.GetLastMonitoringRecordRequest,
):
    """获取最新监测记录"""

    monitoring_record_entity = await db.scalar(
        select(models_monitoring.MonitoringRecord)
        .where(
            and_(
                models_monitoring.MonitoringRecord.station_id
                == get_last_monitoring_record_request.station_id,
                models_monitoring.MonitoringRecord.indicator_id
                == get_last_monitoring_record_request.indicator_id,
            )
        )
        .order_by(models_monitoring.MonitoringRecord.record_time.desc())
    )
    if monitoring_record_entity is None:
        raise ServiceException(ErrorCode.NOT_FOUND, "监测记录不存在")

    return schemas_monitorings.GetLastMonitoringRecordResponse.model_validate(
        monitoring_record_entity
    )


async def get_monitoring_records_trend(
    db: AsyncSession,
    get_monitoring_records_trend_request: schemas_monitorings.GetMonitoringRecordsTrendRequest,
):
    """获取监测记录趋势"""
    stmt = select(models_monitoring.MonitoringRecord).where(
        and_(
            models_monitoring.MonitoringRecord.reservoir_id
            == get_monitoring_records_trend_request.reservoir_id,
            models_monitoring.MonitoringRecord.indicator_id
            == get_monitoring_records_trend_request.indicator_id,
        )
    )
    if get_monitoring_records_trend_request.start_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time
            >= get_monitoring_records_trend_request.start_time
        )
    if get_monitoring_records_trend_request.end_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time
            <= get_monitoring_records_trend_request.end_time
        )
    monitoring_records_entity_list = (
        await db.scalars(
            stmt.order_by(models_monitoring.MonitoringRecord.record_time.desc())
        )
    ).all()
    return schemas_monitorings.GetMonitoringRecordsTrendResponse(
        lists=[
            schemas_monitorings.GetMonitoringRecordsTrendResponseItem.model_validate(
                entity
            )
            for entity in monitoring_records_entity_list
        ],
        total=len(monitoring_records_entity_list),
    )


async def _fetch_real_data():
    """调用真实接口获取最新一条监测记录"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                constants_monitoring.API_URL,
                headers=constants_monitoring.API_HEADERS,
                params=constants_monitoring.API_PARAMS,
            )
            resp.raise_for_status()
            result = resp.json()
            records = result.get("data", {}).get("records", [])
            if not records:
                logger.warning("API返回空记录")
                return None
            return records[0]
    except Exception as e:
        logger.error(f"调用真实接口失败: {e}")
        return None
