from pydantic import BaseModel, Field, ConfigDict


# ========== 辅助类（Support）==========


class ValidateTokenUserItem(BaseModel):
    """验证 token 用户项"""

    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    role_name: str = Field(..., description="用户角色")

    model_config = ConfigDict(from_attributes=True)


# ========== 请求类（Request）==========


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    phone: str | None = Field(None, ge=11, le=11, description="手机号")
    dingtalk_id: str | None = Field(None, description="钉钉ID_用于推送")


class RegisterRequest(BaseModel):
    """注册请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    phone: str | None = Field(None, ge=11, le=11, description="手机号")


# ========== 响应类（Response）==========


class RegisterResponse(BaseModel):
    """注册响应"""

    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str = Field(..., description="访问令牌")
    username: str = Field(..., description="用户名")

    model_config = ConfigDict(from_attributes=True)


class GetCurrentUserDetailResponse(BaseModel):
    """当前用户详情响应"""

    user_id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色")
    phone: str | None = Field(None, ge=11, le=11, description="手机号")
    dingtalk_id: str | None = Field(None, description="钉钉ID_用于推送")

    model_config = ConfigDict(from_attributes=True)
