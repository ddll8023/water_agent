"""报告生成记录模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, JSON
from app.core.database import Base


class Report(Base):
    __tablename__ = "report"

    __table_args__ = {"mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="报告ID")
    title = Column(String(200), nullable=False, comment="报告标题")
    report_type = Column(String(20), nullable=False, comment="报告类型: daily/quarterly/event")
    status = Column(String(20), nullable=False, default="draft", comment="状态: draft/published/no_data")
    summary = Column(Text, nullable=True, comment="AI 生成摘要")
    sections = Column(JSON, nullable=True, comment="结构化章节 [{title, content}]")
    conclusion = Column(Text, nullable=True, comment="总体结论与建议")
    period_start = Column(DateTime, nullable=False, comment="数据覆盖起始时间")
    period_end = Column(DateTime, nullable=False, comment="数据覆盖结束时间")
    generated_by = Column(Integer, nullable=True, comment="手动触发时操作用户ID")
    reservoir_ids = Column(JSON, nullable=True, comment="覆盖水库ID列表")
    reviewed_by = Column(Integer, nullable=True, comment="审核人ID")
    review_comment = Column(Text, nullable=True, comment="审核意见")
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
