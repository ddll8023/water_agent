from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


class ChatItem(BaseModel):
    """对话信息"""

    message_id: int = Field(..., alias="id", description="消息 Id")
    role: str = Field(..., description="角色：user / assistant")
    content: str = Field(..., description="消息内容")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ReSortResultItem(BaseModel):
    """重排序ai返回结果信息"""

    index: int = Field(..., description="文档在原列表中的序号（从0开始）")
    score: int = Field(..., ge=1, le=5, description="相关性得分（1-5）")
    reason: str = Field(..., description="简短打分理由")

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """对话请求"""

    query: str = Field(..., description="用户消息")
    session_id: int | None = Field(description="对话会话id")


class GetChatListRequest(BaseModel):
    """获取对话列表请求"""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=10)


class ReChatRequest(BaseModel):
    """重试/修改对话请求"""

    session_id: int = Field(..., description="session Id")
    message_id: int = Field(..., description="修改的消息Id")
    query: str = Field(..., description="用户消息")


class GetChatListResponse(BaseModel):
    """获取对话列表响应"""

    id: int = Field(..., description="session Id")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class GetChatDetailResponse(BaseModel):
    """获取对话详情响应"""

    id: int = Field(..., description="session Id")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: list[ChatItem] = Field(default_factory=list, description="消息列表")

    model_config = ConfigDict(from_attributes=True)
