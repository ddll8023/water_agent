from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


class ChatRequest(BaseModel):
    """对话请求"""

    query: str = Field(..., description="用户消息")
    session_id: int | None = Field(description="对话会话id")
