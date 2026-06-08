"""仪表盘总览统计服务"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import monitoring as models_monitoring
from app.models import station as models_station
from app.models import reservoir as models_reservoir
from app.models import indicator as models_indicator
from app.schemas import dashboard as schemas_dashboard
from app.models import alert as models_alert
from app.core.redis import get_redis, Redis, is_redis_available
import json


async def get_dashboard_overview(db: AsyncSession):
    """获取仪表盘总览统计"""
    reservoir_count = await db.scalar(
        select(func.count(models_reservoir.Reservoir.id)).where(
            models_reservoir.Reservoir.status == 1
        )
    )
    normal_count = await db.scalar(
        select(func.count(models_station.MonitoringStation.id)).where(
            models_station.MonitoringStation.status == 1
        )
    )
    abnormal_count = await db.scalar(
        select(func.count(models_monitoring.MonitoringRecord.id)).where(
            models_monitoring.MonitoringRecord.quality_flag == 0
        )
    )
    alert_count = await db.scalar(
        select(func.count(models_monitoring.MonitoringRecord.id)).where(
            models_monitoring.MonitoringRecord.quality_flag.in_([0, 2])
        )
    )
    offline_stations = await db.scalar(
        select(func.count(models_station.MonitoringStation.id)).where(
            models_station.MonitoringStation.status == 0
        )
    )
    return schemas_dashboard.GetDashboardOverviewResponse(
        reservoir_count=reservoir_count or 0,
        normal_count=normal_count or 0,
        abnormal_count=abnormal_count or 0,
        alert_count=alert_count or 0,
        offline_stations=offline_stations or 0,
    )


async def get_reservoir_cards(db: AsyncSession):
    """获取水库卡片列表（含核心指标最新值）"""
    station_total = (
        select(func.count(models_station.MonitoringStation.id))
        .where(
            models_station.MonitoringStation.reservoir_id
            == models_reservoir.Reservoir.id
        )
        .correlate(models_reservoir.Reservoir)
        .scalar_subquery()
    )
    station_online = (
        select(func.count(models_station.MonitoringStation.id))
        .where(
            models_station.MonitoringStation.reservoir_id
            == models_reservoir.Reservoir.id,
            models_station.MonitoringStation.status == 1,
        )
        .correlate(models_reservoir.Reservoir)
        .scalar_subquery()
    )
    alert_sub = (
        select(func.count(models_monitoring.MonitoringRecord.id))
        .where(
            models_monitoring.MonitoringRecord.reservoir_id
            == models_reservoir.Reservoir.id,
            models_monitoring.MonitoringRecord.quality_flag != 1,
        )
        .correlate(models_reservoir.Reservoir)
        .scalar_subquery()
    )

    stmt = (
        select(
            models_reservoir.Reservoir.id,
            models_reservoir.Reservoir.name,
            models_reservoir.Reservoir.code,
            models_reservoir.Reservoir.location,
            models_reservoir.Reservoir.water_grade,
            models_reservoir.Reservoir.watershed,
            station_total.label("station_count"),
            station_online.label("online_station_count"),
            alert_sub.label("alert_count"),
        )
        .where(
            models_reservoir.Reservoir.status == 1,
        )
        .order_by(
            models_reservoir.Reservoir.sort_order,
        )
    )

    reservoir_rows = (await db.execute(stmt)).all()

    core_indicator_ids = (
        await db.scalars(
            select(models_indicator.Indicator.id).where(
                models_indicator.Indicator.is_core == 1
            )
        )
    ).all()

    if not reservoir_rows or not core_indicator_ids:
        return []

    reservoir_ids = [row.id for row in reservoir_rows]

    ranked = (
        select(
            models_monitoring.MonitoringRecord.reservoir_id,
            models_monitoring.MonitoringRecord.indicator_id,
            models_monitoring.MonitoringRecord.value,
            models_indicator.Indicator.name,
            models_indicator.Indicator.code,
            models_indicator.Indicator.unit,
            func.row_number()
            .over(
                partition_by=[
                    models_monitoring.MonitoringRecord.reservoir_id,
                    models_monitoring.MonitoringRecord.indicator_id,
                ],
                order_by=models_monitoring.MonitoringRecord.record_time.desc(),
            )
            .label("rn"),
        )
        .join(
            models_indicator.Indicator,
            models_monitoring.MonitoringRecord.indicator_id
            == models_indicator.Indicator.id,
        )
        .where(
            models_monitoring.MonitoringRecord.reservoir_id.in_(reservoir_ids),
            models_monitoring.MonitoringRecord.indicator_id.in_(core_indicator_ids),
        )
        .subquery()
    )

    latest_indicator_rows = (
        await db.execute(
            select(
                ranked.c.reservoir_id,
                ranked.c.indicator_id,
                ranked.c.value,
                ranked.c.name,
                ranked.c.code,
                ranked.c.unit,
            ).where(ranked.c.rn == 1)
        )
    ).all()

    ind_map: dict[int, list] = {}
    for row in latest_indicator_rows:
        ind_map.setdefault(row.reservoir_id, []).append(
            schemas_dashboard.ReservoirCardIndicatorItem(
                name=row.name,
                code=row.code,
                value=str(round(row.value, 4)) if row.value is not None else None,
                unit=row.unit,
            )
        )

    return [
        schemas_dashboard.ReservoirCardResponse(
            id=row.id,
            name=row.name,
            code=row.code,
            location=row.location,
            water_grade=row.water_grade,
            watershed=row.watershed,
            station_count=row.station_count or 0,
            online_station_count=row.online_station_count or 0,
            alert_count=row.alert_count or 0,
            indicators=ind_map.get(row.id, []),
        )
        for row in reservoir_rows
    ]


async def get_last_alert(
    db: AsyncSession,
):
    """获取最近告警记录"""
    if await is_redis_available():
        redis_client = await get_redis()
        alert_list = await redis_client.lrange("alert:recent", 0, -1)
        if alert_list:
            return [
                schemas_dashboard.GetLastAlertResponse.model_validate(json.loads(alert))
                for alert in alert_list
            ]

    alert_entity_list = await db.scalars(
        select(models_alert.AlertEvent)
        .order_by(models_alert.AlertEvent.detected_at.desc())
        .limit(5)
    )
    return [
        schemas_dashboard.GetLastAlertResponse.model_validate(row)
        for row in alert_entity_list
    ]
