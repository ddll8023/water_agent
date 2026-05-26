from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class GetRoleListRequest(BaseModel):
    """角色列表请求"""

    page: int | None = Field(1, ge=1, description="页码")
    page_size: int | None = Field(10, ge=10, description="每页数量")


class GetRoleListResponse(BaseModel):
    """角色列表响应"""

    id: int = Field(..., description="角色 ID")
    role_name: str = Field(..., validation_alias="name", description="角色名称")
    created_at: datetime | None = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)
