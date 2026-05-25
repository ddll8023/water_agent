from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ========== 请求类（Request）==========


class GetUserListRequest(BaseModel):
    """用户列表请求"""

    keyword: str | None = Field(None, description="搜索关键词")
    role_id: int | None = Field(None, description="角色 ID")
    status: int | None = Field(None, description="状态")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=10, description="每页数量")


# ========== 响应类（Response）==========


class GetUserListResponse(BaseModel):
    """用户列表项响应"""

    id: int = Field(..., description="用户 ID")
    role_id: int = Field(..., description="角色 ID")
    username: str = Field(..., description="用户名")
    real_name: str | None = Field(None, description="真实姓名")
    phone: str | None = Field(None, description="手机号")
    dingtalk_id: str | None = Field(None, description="钉钉ID_用于推送")
    status: int = Field(..., description="状态")
    last_login: datetime | None = Field(None, description="最后登录时间")

    model_config = ConfigDict(from_attributes=True)
