"""AI 趋势分析摘要记录模型"""

from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, BigInteger, ForeignKey, JSON

from app.core.database import Base


class PatrolAnalysis(Base):
    __tablename__ = "patrol_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分析ID")
    reservoir_id = Column(
        Integer,
        ForeignKey("reservoir.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="水库ID（故障记录为 None）",
    )
    analyzed_at = Column(DateTime, nullable=False, comment="分析执行时间")
    period_start = Column(DateTime, nullable=False, comment="覆盖开始时间")
    period_end = Column(DateTime, nullable=False, comment="覆盖结束时间")
    summary = Column(Text, nullable=False, comment="AI 分析摘要")
    supplementary_alert_ids = Column(JSON, nullable=True, comment="本次分析创建的 AI 预警 ID 列表")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
