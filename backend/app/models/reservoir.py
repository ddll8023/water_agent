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


class Reservoir(Base):
    __tablename__ = "reservoir"

    id = Column[int](Integer, primary_key=True, index=True, comment="水库ID")
    name = Column[str](String(255), nullable=False, comment="水库名称")
    code = Column[str](String(50), nullable=False, comment="水库编号")
    location = Column[str](String(255), comment="所在位置")
    longitude = Column[str](String(50), comment="经度")
    latitude = Column[str](String(50), comment="纬度")
    capacity = Column[str](String(50), comment="库容_万m3")  # 使用字符串存储以保留单位
    water_grade = Column[str](String(50), comment="水质等级_Ⅱ类_Ⅲ类")
    watershed = Column[str](String(255), comment="所属流域")
    sort_order = Column[int](Integer, default=0, comment="排序")
    status = Column[int](SmallInteger, default=1, comment="0停用_1启用")  # 0停用, 1启用
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column[datetime](
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    __table_args__ = (Index("idx_reservoir_code", code, unique=True),)
