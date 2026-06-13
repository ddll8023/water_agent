from sqlalchemy import Column, Integer, Text, DateTime, BigInteger, ForeignKey
from app.core.database import Base
from datetime import datetime


class PatrolAnalysis(Base):
    __tablename__ = "patrol_analysis"

    id = Column[int](BigInteger, primary_key=True, autoincrement=True, comment="分析ID")
    reservoir_id = Column[int](
        Integer,
        ForeignKey("reservoir.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="水库ID",
    )
    analyzed_at = Column[datetime](DateTime, nullable=False, comment="分析执行时间")
    period_start = Column[datetime](DateTime, nullable=False, comment="覆盖开始时间")
    period_end = Column[datetime](DateTime, nullable=False, comment="覆盖结束时间")
    summary = Column[str](Text, nullable=False, comment="AI 分析摘要")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")
