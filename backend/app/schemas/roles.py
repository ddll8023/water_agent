from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========


class GetRoleListRequest(BaseModel):
    """角色列表请求"""

    keyword: str | None = Field(None, description="搜索关键词")

    page: int | None = Field(1, ge=1, description="页码")
    page_size: int | None = Field(10, ge=10, description="每页数量")


class AddRoleRequest(BaseModel):
    """添加角色请求"""

    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    permissions: dict = Field(default_factory=dict, description="权限列表")


class UpateRoleRequest(BaseModel):
    """更新角色请求"""

    id: int = Field(..., description="角色 ID")
    name: str | None = Field(None, description="角色名称")
    code: str | None = Field(None, description="角色编码")
    permissions: dict = Field(default_factory=dict, description="权限列表")


# ========== 响应类（Response）==========


class GetRoleListResponse(BaseModel):
    """角色列表响应"""

    id: int = Field(..., description="角色 ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    created_at: datetime | None = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class AddRoleResponse(BaseModel):
    """添加角色响应"""

    id: int = Field(..., description="角色 ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    permissions: dict = Field(default_factory=dict, description="权限列表")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class GetRoleDetailResponse(BaseModel):
    """获取角色详情响应"""

    id: int = Field(..., description="角色 ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    permissions: dict = Field(default_factory=dict, description="权限列表")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)
