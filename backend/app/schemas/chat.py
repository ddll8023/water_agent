from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


class ChatRequest(BaseModel):
    """对话请求"""

    query: str = Field(..., description="用户消息")
    session_id: int | None = Field(description="对话会话id")


class GetChatListRequest(BaseModel):
    """获取对话列表请求"""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=10)


class GetChatListResponse(BaseModel):
    """获取对话列表响应"""

    id: int = Field(..., description="session Id")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)
