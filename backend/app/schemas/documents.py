from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field

# ========== 辅助类（Support）==========


class DocumentType(IntEnum):
    """知识库文档类型"""

    STANDARD = 0
    CASE = 1
    SOP = 2
    OTHER = 3


class DocumentStatus(IntEnum):
    """文档处理状态"""

    ALREADY = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


class UploadDocumentItem(BaseModel):
    """批量上传单项结果"""

    document_id: int = Field(description="文档ID（校验失败为0）")
    file_name: str = Field(description="原始文件名")
    file_size: int = Field(description="文件大小（字节）")
    status: int = Field(description="处理状态：0=校验失败 1=处理中")
    error: str | None = Field(None, description="校验失败原因")

    model_config = ConfigDict(from_attributes=True)


# ========== 请求类（Request）==========


class GetDocumentListRequest(BaseModel):
    """获取知识库文档列表请求参数"""

    keyword: str | None = Field(None, description="文件名关键字")
    doc_type: int | None = Field(
        None, description="文档类型：0=标准 1=案例 2=预案 3=其他"
    )
    status: int | None = Field(None, description="处理状态：0=处理中 1=就绪 2=失败")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")


# ========== 响应类（Response）==========


class UploadDocumentResponse(BaseModel):
    """批量上传整体响应"""

    total: int = Field(description="总文件数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    lists: list[UploadDocumentItem] = Field(
        default_factory=list, description="逐文件结果"
    )

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentItem(BaseModel):
    """知识库文档列表项响应"""

    id: int = Field(description="文档ID")
    title: str | None = Field(None, description="文档标题")
    file_name: str = Field(description="原始文件名")
    file_size: int = Field(description="文件大小（字节）")
    doc_type: int = Field(description="文档类型：0=标准 1=案例 2=预案 3=其他")
    status: int = Field(description="处理状态：0=处理中 1=就绪 2=失败")
    chunk_count: int = Field(description="切片数量")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetail(BaseModel):
    """知识库文档详情响应"""

    id: int = Field(description="文档ID")
    title: str | None = Field(None, description="文档标题")
    file_name: str = Field(description="原始文件名")
    file_size: int = Field(description="文件大小（字节）")
    doc_type: int = Field(description="文档类型：0=标准 1=案例 2=预案 3=其他")
    status: int = Field(description="处理状态：0=处理中 1=就绪 2=失败")
    chunk_count: int = Field(description="切片数量")
    content: str | None = Field(None, description="解析后的文本内容")
    metadata: dict | None = Field(None, description="元数据：来源/日期/标签等")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    model_config = ConfigDict(from_attributes=True)
