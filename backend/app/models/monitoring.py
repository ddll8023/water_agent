from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    SmallInteger,
    Index,
    DECIMAL,
)
from app.core.database import Base
from datetime import datetime


class MonitoringRecord(Base):
    __tablename__ = "monitoring_record"
    """监测记录表"""

    id = Column[int](
        Integer, primary_key=True, autoincrement=True, comment="监测记录ID"
    )
    reservoir_id = Column[int](Integer, ForeignKey("reservoir.id"), comment="水库ID")
    station_id = Column[int](
        Integer, ForeignKey("monitoring_station.id"), comment="站点ID"
    )
    indicator_id = Column[int](Integer, ForeignKey("indicator.id"), comment="指标ID")
    value = Column[float](DECIMAL(10, 4), comment="监测值")
    data_source = Column[str](String(50), comment="数据来源：auto/manual/import")
    quality_flag = Column[int](SmallInteger, default=1, comment="0可疑_1正常_2无效")
    record_time = Column[datetime](DateTime, comment="监测时间")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_reservoir_time", reservoir_id, record_time),
        Index("idx_station_time", station_id, record_time),
        Index("idx_indicator_time", indicator_id, record_time),
    )
