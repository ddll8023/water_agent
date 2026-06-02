"""仪表盘总览统计服务"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import monitoring as models_monitoring
from app.models import station as models_station
from app.models import reservoir as models_reservoir
from app.schemas import dashboard as schemas_dashboard


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
