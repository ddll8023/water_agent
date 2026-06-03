from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    SmallInteger,
    Index,
    DECIMAL,
)
from app.core.database import Base
from datetime import datetime


class Indicator(Base):
    __tablename__ = "indicator"
    id = Column[int](Integer, primary_key=True, comment="指标ID")
    name = Column[str](String(255), nullable=False, comment="指标名称")
    code = Column[str](String(50), nullable=False, comment="指标编码")
    unit = Column[str](String(50), comment="单位_mg_L")
    category = Column[str](String(50), comment="分类_物理_化学_生物")
    standard_limit_i_lower = Column[float](DECIMAL(10, 2), comment="Ⅰ类下限值")
    standard_limit_i_upper = Column[float](DECIMAL(10, 2), comment="Ⅰ类上限值")
    standard_limit_ii_lower = Column[float](DECIMAL(10, 2), comment="Ⅱ类下限值")
    standard_limit_ii_upper = Column[float](DECIMAL(10, 2), comment="Ⅱ类上限值")
    standard_limit_iii_lower = Column[float](DECIMAL(10, 2), comment="Ⅲ类下限值")
    standard_limit_iii_upper = Column[float](DECIMAL(10, 2), comment="Ⅲ类上限值")
    standard_limit_iv_lower = Column[float](DECIMAL(10, 2), comment="Ⅳ类下限值")
    standard_limit_iv_upper = Column[float](DECIMAL(10, 2), comment="Ⅳ类上限值")
    standard_limit_v_lower = Column[float](DECIMAL(10, 2), comment="Ⅴ类下限值")
    standard_limit_v_upper = Column[float](DECIMAL(10, 2), comment="Ⅴ类上限值")
    is_core = Column[int](SmallInteger, default=0, comment="是否核心指标，0否_1是")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column[datetime](
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    __table_args__ = (
        Index("idx_indicator_code", code, unique=True),
        Index("idx_indicator_name", name),
    )
