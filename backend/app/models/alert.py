from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from app.core.database import Base
from datetime import datetime

"""
alert_event {
    int id PK
    int reservoir_id FK
    int handler_id FK "处理人"
    varchar title "预警标题"
    varchar alert_level "info_warning_critical"
    json indicators "超标指标JSON_name_value_limit"
    varchar source_desc "溯源描述"
    varchar suggestion "处置建议"
    varchar status "new_confirmed_processing_resolved"
    datetime detected_at "检出时间"
    datetime resolved_at "解决时间"
    datetime created_at
}
"""


class AlertEvent(Base):
    __tablename__ = "alert_event"

    id = Column[int](Integer, primary_key=True, autoincrement=True, comment="预警ID")
    reservoir_id = Column[int](
        Integer, ForeignKey("reservoir.id"), index=True, nullable=False, comment="水库ID"
    )
    handler_id = Column[int](
        Integer, ForeignKey("user.id"), index=True, comment="处理人ID"
    )
    title = Column[str](String(255), nullable=False, comment="预警标题")
    alert_level = Column[str](String(50), nullable=False, comment="预警等级_info_warning_critical")
    indicators = Column(JSON, comment="超标指标列表_name_value_limit")
    source_desc = Column[str](Text, comment="溯源描述")
    suggestion = Column[str](Text, comment="处置建议")
    status = Column[str](String(50), nullable=False, default="new", index=True, comment="状态_new_confirmed_processing_resolved")
    detected_at = Column[datetime](DateTime, nullable=False, comment="检出时间")
    resolved_at = Column[datetime](DateTime, comment="解决时间")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_alert_reservoir_status", reservoir_id, status),
        Index("idx_alert_detected_at", detected_at),
    )
