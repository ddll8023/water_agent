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
from app.models.role import Role


class User(Base):
    __tablename__ = "user"
    id = Column[int](Integer, primary_key=True, autoincrement=True, comment="用户ID")
    role_id = Column[int](
        Integer,
        ForeignKey("role.id", ondelete="SET NULL"),
        comment="角色ID",
    )
    username = Column[str](String(256), nullable=False, comment="用户名")
    password = Column[str](String(256), nullable=False, comment="密码哈希")
    real_name = Column[str](String(64), comment="真实姓名")
    phone = Column[str](String(11), comment="手机号")
    dingtalk_id = Column[str](String(256), comment="钉钉ID_用于推送")
    status = Column[int](SmallInteger, default=1, comment="0禁用_1启用")
    last_login = Column[datetime](DateTime, comment="最后登录时间")
    created_at = Column[datetime](DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column[datetime](
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    __table_args__ = (
        Index("idx_user_username", username, unique=True),
        Index("idx_user_role_id", role_id),
    )
