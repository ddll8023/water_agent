from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    func,
)
from app.core.database import Base
from datetime import datetime


class ChatSession(Base):
    """对话：存储用户的问答对话会话"""

    __tablename__ = "chat_session"

    id = Column[int](BigInteger, primary_key=True, autoincrement=True, comment="对话ID")
    user_id = Column[int](
        Integer,
        ForeignKey("user.id"),
        index=True,
        comment="用户ID（为空表示匿名对话）",
    )
    title = Column[str](String(255), comment="对话标题（首次query前30字）")
    message_list = Column[list](
        JSON, default=list, comment="消息滑动窗口，包含最近的message_id列表"
    )
    status = Column[int](
        SmallInteger,
        default=0,
        index=True,
        comment="状态：0=活跃 1=归档",
    )
    created_at = Column[datetime](
        DateTime,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at = Column[datetime](
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
