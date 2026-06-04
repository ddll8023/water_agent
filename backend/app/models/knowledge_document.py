"""知识库文档模型"""

from sqlalchemy import (
    Column,
    BigInteger,
    SmallInteger,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    func,
)
from app.core.database import Base
from datetime import datetime


class KnowledgeDocument(Base):
    """知识库文档：存储上传的标准/案例/预案等文档元信息与解析内容"""

    __tablename__ = "knowledge_document"

    id = Column[int](BigInteger, primary_key=True, autoincrement=True, comment="主键")
    title = Column[str](String(255), nullable=True, comment="文档标题")
    doc_type = Column[int](
        SmallInteger,
        default=0,
        index=True,
        comment="文档类型：0=标准 1=案例 2=预案 3=其他",
    )
    file_name = Column[str](String(255), nullable=False, comment="原始文件名")
    file_path = Column[str](String(500), nullable=False, comment="服务器存储路径")
    file_size = Column[int](BigInteger, default=0, comment="文件大小（字节）")
    content = Column[str](Text, comment="解析后的纯文本内容")
    chunk_count = Column[int](Integer, default=0, comment="Chroma 切片数量")
    status = Column[int](
        SmallInteger,
        default=0,
        index=True,
        comment="处理状态：0=已入库，1=解析中，2=已完成，3=失败",
    )
    error = Column[str](Text, comment="解析错误原因")
    created_at = Column[datetime](
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at = Column[datetime](
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
