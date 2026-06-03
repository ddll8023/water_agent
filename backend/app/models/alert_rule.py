from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from app.core.database import Base
from datetime import datetime


class AlertRule(Base):
    __tablename__ = "alert_rule"

    id = Column[int](Integer, primary_key=True, autoincrement=True, comment="规则ID")
    rule_name = Column[str](String(255), nullable=False, comment="规则名称")
    indicator_id = Column[int](
        Integer,
        ForeignKey("indicator.id"),
        nullable=False,
        index=True,
        comment="关联指标ID",
    )
    reservoir_id = Column[int](
        Integer,
        ForeignKey("reservoir.id"),
        nullable=True,
        index=True,
        comment="水库ID，null=全局规则",
    )
    compare_direction = Column[str](
        String(10),
        nullable=False,
        default="gt",
        comment="比较方向：gt=超上限告警 lt=低下限告警",
    )
    trigger_class = Column[str](
        String(10), nullable=False, comment="触发限值等级：I/II/III/IV/V"
    )
    alert_level = Column[int](
        SmallInteger,
        nullable=False,
        comment="预警等级：1=info 2=warning 3=critical",
    )
    is_active = Column[int](
        SmallInteger, default=1, comment="是否启用：0禁用 1启用"
    )
    remark = Column[str](Text, comment="备注说明")

    created_at = Column[datetime](
        DateTime, default=datetime.now, comment="创建时间"
    )
    updated_at = Column[datetime](
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )
