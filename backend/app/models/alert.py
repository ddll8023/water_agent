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
    text,
)
from app.core.database import Base
from datetime import datetime


class AlertEvent(Base):
    __tablename__ = "alert_event"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="预警ID")
    reservoir_id = Column(
        Integer,
        ForeignKey("reservoir.id"),
        index=True,
        nullable=False,
        comment="水库ID",
    )
    handler_id = Column(
        Integer,
        ForeignKey("user.id"),
        index=True,
        comment="处理人ID",
    )
    title = Column(String(255), nullable=False, comment="预警标题")
    alert_level = Column(
        SmallInteger, nullable=False, comment="预警等级：1=info 2=warning 3=critical"
    )
    indicators = Column(
        JSON, default=list, comment="超标指标列表_name_value_limit"
    )
    source_desc = Column(Text, comment="溯源描述")
    suggestion = Column(JSON, comment="处置建议")
    suggestion_status = Column(
        SmallInteger, default=0, nullable=False, server_default=text("0"),
        index=True, comment="建议状态_0=无_1=生成中_2=已生成_3=已确认"
    )
    notes = Column(
        JSON, default=list, comment="处置备注列表_id_user_id_content_created_at"
    )
    status = Column(
        SmallInteger,
        nullable=False,
        default=0,
        index=True,
        comment="状态_0=待确认_1=已确认_2=处置中_3=已解决",
    )
    source = Column(
        SmallInteger, nullable=False, default=0, comment="来源_0=规则判定_1=Agent趋势分析"
    )
    detected_at = Column(DateTime, nullable=False, comment="检出时间")
    resolved_at = Column(DateTime, comment="解决时间")
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    __table_args__ = (
        Index("idx_alert_reservoir_status", reservoir_id, status),
        Index("idx_alert_detected_at", detected_at),
    )
