from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    SmallInteger,
    Index,
)
from app.core.database import Base
from datetime import datetime

"""
monitoring_station {
        int id PK
        int reservoir_id FK
        varchar name "站点名称"
        varchar code "站点编号"
        varchar type "auto自动站_manual人工_sensing遥感"
        decimal longitude "经度"
        decimal latitude "纬度"
        varchar sampling_point "采样点位描述"
        tinyint status "0离线_1在线"
        datetime last_data_time "最后数据时间"
        datetime created_at
    }
"""


class MonitoringStation(Base):
    __tablename__ = "monitoring_station"

    id = Column[int](Integer, primary_key=True, comment="主键 ID")
    reservoir_id = Column[int](
        Integer, ForeignKey("reservoir.id", ondelete="SET NULL"), comment="水库ID"
    )
    name = Column[str](String(255), nullable=False, comment="站点名称")
    code = Column[str](String(255), nullable=False, comment="站点编号")
    type = Column[str](String(255), comment="站点类型")
    longitude = Column[str](String(50), comment="经度")
    latitude = Column[str](String(50), comment="纬度")
    sampling_point = Column[str](String(255), comment="采样点位描述")
    status = Column[int](SmallInteger, default=1, comment="0离线_1在线")
    last_data_time = Column[datetime](DateTime, comment="最后数据时间")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column[datetime](
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    __table_args__ = (
        Index("ix_monitoring_station_reservoir_id", reservoir_id),
        Index("ix_monitoring_station_code", code, unique=True),
        Index("ix_monitoring_station_name", name),
    )
