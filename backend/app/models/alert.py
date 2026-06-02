from typing import Any


from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from app.core.database import Base
from datetime import datetime


class AlertEvent(Base):
    __tablename__ = "alert_event"

    id = Column[int](Integer, primary_key=True, autoincrement=True, comment="预警ID")
    reservoir_id = Column[int](
        Integer,
        ForeignKey("reservoir.id"),
        index=True,
        nullable=False,
        comment="水库ID",
    )
    handler_id = Column[int](
        Integer, ForeignKey("user.id"), index=True, comment="处理人ID"
    )
    title = Column[str](String(255), nullable=False, comment="预警标题")
    alert_level = Column[str](
        String(50), nullable=False, comment="预警等级_info_warning_critical"
    )
    indicators = Column[list[dict]](JSON, comment="超标指标列表_name_value_limit")
    source_desc = Column[str](Text, comment="溯源描述")
    suggestion = Column[str](Text, comment="处置建议")
    status = Column[int](
        SmallInteger,
        nullable=False,
        default=0,
        index=True,
        comment="状态_0=待确认_1=已确认_2=处置中_3=已解决",
    )
    detected_at = Column[datetime](DateTime, nullable=False, comment="检出时间")
    resolved_at = Column[datetime](DateTime, comment="解决时间")

    __table_args__ = (
        Index("idx_alert_reservoir_status", reservoir_id, status),
        Index("idx_alert_detected_at", detected_at),
    )
