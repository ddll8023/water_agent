from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, BigInteger
from app.core.database import Base
from datetime import datetime


class PatrolLog(Base):
    __tablename__ = "patrol_log"

    id = Column[int](BigInteger, primary_key=True, autoincrement=True, comment="巡检日志ID")
    executed_at = Column[datetime](DateTime, nullable=False, comment="执行开始时间")
    status = Column[int](
        SmallInteger, nullable=False, default=0, index=True, comment="执行状态_0=成功_1=部分失败_2=失败_3=无数据"
    )
    station_count = Column[int](Integer, nullable=False, default=0, comment="在线站点数")
    record_count = Column[int](Integer, nullable=False, default=0, comment="入库记录数")
    new_alert_count = Column[int](Integer, nullable=False, default=0, comment="新增预警数")
    merge_count = Column[int](Integer, nullable=False, default=0, comment="合并预警数")
    duration_ms = Column[int](Integer, nullable=False, default=0, comment="执行耗时_毫秒")
    error = Column[str](String(500), comment="错误信息")
    created_at = Column[datetime](
        DateTime, default=datetime.now, comment="创建时间"
    )
