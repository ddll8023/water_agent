from sqlalchemy import (
    Column,
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


class ChatMessage(Base):
    """消息：存储对话中的单条消息"""

    __tablename__ = "chat_message"

    id = Column[int](BigInteger, primary_key=True, autoincrement=True, comment="消息ID")
    session_id = Column[int](
        BigInteger,
        ForeignKey("chat_session.id"),
        nullable=False,
        index=True,
        comment="对话ID",
    )
    role = Column[str](String(16), nullable=False, comment="角色：user / assistant")
    content = Column[str](Text, nullable=False, comment="消息内容")
    reference = Column[list[dict]](JSON, comment="参考信息内容,{doc_id,chunk_index}")
    status = Column[int](
        SmallInteger,
        default=0,
        index=True,
        comment="状态：0=活跃 1=已废弃（被重试替换）",
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

    __table_args__ = (Index("idx_message_session_created", session_id, created_at),)
