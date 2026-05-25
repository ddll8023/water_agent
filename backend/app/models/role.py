from typing import Any


from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from app.core.database import Base
from datetime import datetime


class Role(Base):
    __tablename__ = "role"

    id = Column[int](Integer, primary_key=True, autoincrement=True, comment="角色ID")
    name = Column[str](String(50), nullable=False, comment="角色名称")
    code = Column[str](String(50), unique=True, nullable=False, comment="角色编码")
    permissions = Column[dict](JSON, comment="权限列表")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_role_code", code),
        Index("idx_role_name", name),
    )
