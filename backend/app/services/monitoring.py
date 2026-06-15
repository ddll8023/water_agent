"""监测数据定时采集与查询服务"""

import json
import math
import random
import httpx
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_or_rollback, get_background_db_session
from app.core.redis import get_redis, is_redis_available
from app.models import monitoring as models_monitoring
from app.models import station as models_station
from app.models import indicator as models_indicator
from app.constants import monitoring as constants_monitoring
from app.utils.logger_config import setup_logger
from app.schemas import monitorings as schemas_monitorings
from app.schemas.common import PaginationInfo, PaginatedResponse, ErrorCode
from app.utils.exception import ServiceException
from app.states.monitoring import ProcessResult
from redis import Redis

logger = setup_logger(__name__)


async def process_and_save_data(db: AsyncSession, raw_data: dict):
    """处理并入库一条监测记录（按 station_code 匹配站点），返回处理统计"""
    station_code = raw_data.get("station_code")
    if not station_code:
        return ProcessResult(
            station_count=0,
            record_count=0,
            pending_alerts=[],
            cached_records=[],
            error_info="缺少 station_code",
        )

    station = await db.scalar(
        select(models_station.MonitoringStation).where(
            models_station.MonitoringStation.code == station_code,
            models_station.MonitoringStation.status == 1,
        )
    )
    if not station:
        return ProcessResult(
            station_count=0,
            record_count=0,
            pending_alerts=[],
            cached_records=[],
            error_info=f"站点 {station_code} 不存在或离线",
        )

    monitor_time_str = raw_data.get("monitorTime")
    monitor_time = (
        datetime.strptime(monitor_time_str, "%Y-%m-%d %H:%M:%S")
        if monitor_time_str
        else datetime.now()
    )

    indicator_entity_list = (await db.scalars(select(models_indicator.Indicator))).all()
    indicator_code_dict = {item.code: item for item in indicator_entity_list}

    total_records = 0
    cached_records: list[dict] = []
    pending_alerts: list[dict] = []

    for field, raw_value in raw_data.items():
        if field in ("station_code", "monitorTime"):
            continue
        indicator_entity = indicator_code_dict.get(field)
        if indicator_entity is None:
            continue
        indicator_id = indicator_entity.id

        existing = await db.scalar(
            select(models_monitoring.MonitoringRecord).where(
                and_(
                    models_monitoring.MonitoringRecord.station_id == station.id,
                    models_monitoring.MonitoringRecord.indicator_id == indicator_id,
                    models_monitoring.MonitoringRecord.record_time == monitor_time,
                )
            )
        )
        if existing is not None:
            continue

        db.add(
            models_monitoring.MonitoringRecord(
                reservoir_id=station.reservoir_id,
                station_id=station.id,
                indicator_id=indicator_id,
                value=raw_value,
                data_source="auto",
                quality_flag=1,
                record_time=monitor_time,
                created_at=datetime.now(),
            )
        )
        total_records += 1

        cached_records.append(
            {
                "reservoir_id": station.reservoir_id,
                "indicator_id": indicator_id,
                "indicator_name": indicator_entity.name,
                "value": raw_value,
                "record_time": monitor_time,
            }
        )

        pending_alerts.append(
            {
                "indicator_id": indicator_id,
                "reservoir_id": station.reservoir_id,
                "value": raw_value,
                "record_time": monitor_time.isoformat(),
            }
        )

    station.last_data_time = monitor_time

    return ProcessResult(
        station_count=1,
        record_count=total_records,
        pending_alerts=pending_alerts,
        cached_records=cached_records,
        error_info=None,
    )


async def get_monitoring_records_list(
    db: AsyncSession,
    request: schemas_monitorings.GetMonitoringRecordsListRequest,
):
    """获取监测记录列表"""
    stmt = select(models_monitoring.MonitoringRecord)
    if request.reservoir_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.reservoir_id == request.reservoir_id
        )
    if request.station_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.station_id == request.station_id
        )
    if request.indicator_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.indicator_id == request.indicator_id
        )
    if request.start_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time >= request.start_time
        )
    if request.end_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time <= request.end_time
        )
    if request.quality_flag is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.quality_flag == request.quality_flag
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    monitoring_records_entity_list = (
        await db.scalars(
            stmt.order_by(models_monitoring.MonitoringRecord.record_time.desc())
            .offset((request.page - 1) * request.page_size)
            .limit(request.page_size)
        )
    ).all()

    return PaginatedResponse(
        lists=[
            schemas_monitorings.GetMonitoringRecordsListResponse.model_validate(entity)
            for entity in monitoring_records_entity_list
        ],
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total,
            total_pages=math.ceil(total / request.page_size) if total else 0,
        ),
    )


async def get_reservoir_latest_indicators(
    db: AsyncSession,
    request: schemas_monitorings.GetReservoirLatestIndicatorsRequest,
):
    """获取水库各指标最新监测值（优先 Redis，回退 MySQL）"""
    reservoir_id = request.reservoir_id

    core_rows = (
        await db.execute(
            select(
                models_indicator.Indicator.id,
                models_indicator.Indicator.name,
            ).where(models_indicator.Indicator.is_core == 1)
        )
    ).all()

    records = []
    fallback_indicator_ids = []
    redis_client: Redis = await get_redis()
    for indicator_id, indicator_name in core_rows:
        key = f"monitoring:last:{reservoir_id}:{indicator_id}"
        try:
            raw = await redis_client.get(key)
        except Exception:
            raw = None

        if raw:
            try:
                data = (
                    json.loads(raw)
                    if isinstance(raw, str)
                    else json.loads(raw.decode())
                )
                records.append(
                    schemas_monitorings.IndicatorLatestValueItem(
                        indicator_id=data["indicator_id"],
                        indicator_name=data["indicator_name"],
                        value=data["value"],
                        quality_flag=data.get("quality_flag", 1),
                        record_time=datetime.fromisoformat(data["record_time"]),
                    )
                )
                continue
            except Exception:
                pass

        fallback_indicator_ids.append(indicator_id)

    if fallback_indicator_ids:
        latest_time_subq = (
            select(
                models_monitoring.MonitoringRecord.indicator_id,
                func.max(models_monitoring.MonitoringRecord.record_time).label(
                    "max_time"
                ),
            )
            .where(
                models_monitoring.MonitoringRecord.reservoir_id == reservoir_id,
                models_monitoring.MonitoringRecord.indicator_id.in_(
                    fallback_indicator_ids
                ),
            )
            .group_by(models_monitoring.MonitoringRecord.indicator_id)
            .subquery()
        )

        stmt = (
            select(
                models_monitoring.MonitoringRecord,
                models_indicator.Indicator.name,
            )
            .join(
                latest_time_subq,
                and_(
                    models_monitoring.MonitoringRecord.indicator_id
                    == latest_time_subq.c.indicator_id,
                    models_monitoring.MonitoringRecord.record_time
                    == latest_time_subq.c.max_time,
                ),
            )
            .join(
                models_indicator.Indicator,
                models_monitoring.MonitoringRecord.indicator_id
                == models_indicator.Indicator.id,
            )
            .where(
                models_monitoring.MonitoringRecord.reservoir_id == reservoir_id,
            )
        )

        rows = (await db.execute(stmt)).all()
        for record_entity, indicator_name in rows:
            records.append(
                schemas_monitorings.IndicatorLatestValueItem(
                    indicator_id=record_entity.indicator_id,
                    indicator_name=indicator_name,
                    value=record_entity.value,
                    quality_flag=record_entity.quality_flag,
                    record_time=record_entity.record_time,
                )
            )

    if not records:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "该水库暂无监测数据")

    records.sort(key=lambda x: x.indicator_id)
    return schemas_monitorings.GetReservoirLatestIndicatorsResponse(
        reservoir_id=reservoir_id,
        records=records,
    )


async def get_monitoring_records_trend(
    db: AsyncSession,
    request: schemas_monitorings.GetMonitoringRecordsTrendRequest,
):
    """获取监测记录趋势：24h 内走 Redis，超范围走 MySQL"""
    now = datetime.now()
    start = request.start_time or (now - timedelta(hours=24))
    end = request.end_time or now
    cutoff_24h = now - timedelta(hours=24)

    if start >= cutoff_24h and request.indicator_id is not None:
        items = await _query_trend_from_redis(
            request.reservoir_id, request.indicator_id, start, end
        )
        if items is not None:
            return schemas_monitorings.GetMonitoringRecordsTrendResponse(
                lists=items, total=len(items)
            )

    stmt = select(models_monitoring.MonitoringRecord).where(
        models_monitoring.MonitoringRecord.reservoir_id == request.reservoir_id,
    )
    if request.indicator_id is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.indicator_id == request.indicator_id,
        )
    if request.start_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time >= request.start_time
        )
    if request.end_time is not None:
        stmt = stmt.where(
            models_monitoring.MonitoringRecord.record_time <= request.end_time
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


async def create_manual_record(
    db: AsyncSession,
    request: schemas_monitorings.ManualInputRequest,
):
    """人工录入一条监测记录"""
    station = await db.get(models_station.MonitoringStation, request.station_id)
    if not station:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "站点不存在")

    indicator = await db.get(models_indicator.Indicator, request.indicator_id)
    if not indicator:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "指标不存在")

    existing = await db.scalar(
        select(models_monitoring.MonitoringRecord).where(
            and_(
                models_monitoring.MonitoringRecord.station_id == request.station_id,
                models_monitoring.MonitoringRecord.indicator_id == request.indicator_id,
                models_monitoring.MonitoringRecord.record_time == request.record_time,
            )
        )
    )
    if existing:
        raise ServiceException(
            ErrorCode.RESOURCE_ALREADY_EXISTS, "该站点+指标+时间已存在记录"
        )

    record = models_monitoring.MonitoringRecord(
        reservoir_id=station.reservoir_id,
        station_id=request.station_id,
        indicator_id=request.indicator_id,
        value=request.value,
        data_source="manual",
        quality_flag=request.quality_flag or 1,
        record_time=request.record_time,
    )
    db.add(record)
    await commit_or_rollback(db)

    await _cache_to_redis(
        reservoir_id=station.reservoir_id,
        indicator_id=request.indicator_id,
        indicator_name=indicator.name,
        value=request.value,
        record_time=request.record_time,
    )

    return schemas_monitorings.GetMonitoringRecordsListResponse.model_validate(record)


"""辅助函数"""


async def _cache_to_redis(
    reservoir_id: int,
    indicator_id: int,
    indicator_name: str,
    value: float,
    record_time: datetime,
):
    """采集一条数据后同步写入 Redis 趋势 ZSET 和最新值 KEY"""
    if not await is_redis_available():
        logger.warning("Redis 不可用，跳过缓存")
        return
    now = datetime.now()
    ts = record_time.timestamp()
    member = json.dumps(
        {"value": value, "record_time": record_time.isoformat(), "quality_flag": 1},
        ensure_ascii=False,
    )

    key_trend = f"monitoring:trend:{reservoir_id}:{indicator_id}"
    key_last = f"monitoring:last:{reservoir_id}:{indicator_id}"
    redis_client: Redis = await get_redis()
    try:
        await redis_client.zadd(key_trend, {member: ts})
        await redis_client.zremrangebyscore(
            key_trend, "-inf", (now - timedelta(hours=24)).timestamp()
        )
        await redis_client.expire(key_trend, 86400)

        last_member = json.dumps(
            {
                "value": value,
                "record_time": record_time.isoformat(),
                "quality_flag": 1,
                "indicator_id": indicator_id,
                "indicator_name": indicator_name,
            },
            ensure_ascii=False,
        )
        await redis_client.set(key_last, last_member, ex=86400)
    except Exception as e:
        logger.error(f"Redis 缓存写入失败: {e}")


async def _query_trend_from_redis(
    reservoir_id: int,
    indicator_id: int,
    start: datetime,
    end: datetime,
):
    """从 Redis 查询时间段内的趋势数据，失败返回 None"""
    key = f"monitoring:trend:{reservoir_id}:{indicator_id}"
    redis_client: Redis = await get_redis()
    try:
        data = await redis_client.zrangebyscore(
            key, start.timestamp(), end.timestamp(), withscores=True
        )
    except Exception:
        logger.error("Redis 趋势查询失败，回退 MySQL")
        return None

    if not data:
        return None

    items = []
    for member, _ in data:
        try:
            parsed = (
                json.loads(member)
                if isinstance(member, str)
                else json.loads(member.decode())
            )
            items.append(
                schemas_monitorings.GetMonitoringRecordsTrendResponseItem(
                    reservoir_id=reservoir_id,
                    indicator_id=indicator_id,
                    record_time=datetime.fromisoformat(parsed["record_time"]),
                    value=parsed["value"],
                )
            )
        except Exception:
            continue

    items.sort(key=lambda x: x.record_time, reverse=True)
    return items


async def _fetch_real_record():
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
            records: list[dict] = result.get("data", {}).get("records", [])
            if not records:
                logger.warning("API返回空记录")
                return None
            return records[0]
    except Exception as e:
        logger.error(f"调用真实接口失败: {e}")
        return None


_MOCK_RANGES = {
    "ph": (6.5, 8.5),
    "rjy": (3.0, 8.0),
    "cod": (5.0, 25.0),
    "ad": (0.1, 1.5),
    "swt": (15, 30),
    "zd": (1, 15),
    "ddl": (200, 600),
    "yl": (0.02, 0.15),
}

MOCK_EXCEED_PROBABILITY = 0.3

_EXCEED_VALUES = {
    "rjy": (2.0, 4.0),
    "cod": (25.0, 45.0),
    "ad": (1.2, 2.5),
    "zd": (15.0, 55.0),
    "ph": (5.0, 6.0),
}


async def _generate_mock_record():
    """模拟模式：优先从真实 API 拿基线数据加偏移，API 不可用时纯随机生成"""
    baseline = await _fetch_real_record()

    async with get_background_db_session() as db:
        station = (
            await db.scalars(
                select(models_station.MonitoringStation).where(
                    models_station.MonitoringStation.status == 1
                )
            )
        ).all()
        if not station:
            return None

        station_code = random.choice(station).code

        if baseline:
            monitor_time = baseline.get("monitorTime")
            mock_record = {"station_code": station_code, "monitorTime": monitor_time}
            for field, value in baseline.items():
                if field in ("monitorTime", "station_code"):
                    continue
                if isinstance(value, (int, float)):
                    offset = random.uniform(-0.05, 0.05)
                    mock_record[field] = round(value * (1 + offset), 4)
                else:
                    mock_record[field] = value
            return mock_record

    # 纯随机 fallback（API 不可用时）
    now = datetime.now()
    mock_record = {
        "station_code": station_code,
        "monitorTime": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    for field, (lo, hi) in _MOCK_RANGES.items():
        mock_record[field] = round(random.uniform(lo, hi), 4)

    if random.random() < MOCK_EXCEED_PROBABILITY:
        exceed_indicator = random.choice(list(_EXCEED_VALUES.keys()))
        lo, hi = _EXCEED_VALUES[exceed_indicator]
        mock_record[exceed_indicator] = round(random.uniform(lo, hi), 4)

    return mock_record
