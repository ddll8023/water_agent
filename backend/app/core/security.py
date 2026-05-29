from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timezone
from app.core.database import get_db
from app.models import user as models_user
from app.schemas import auth as schemas_auth

# Bearer token 方案
oahth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict):
    """创建 access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str):
    """验证 token"""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token 验证失败")


def get_current_user(
    token: str = Depends(oahth2_scheme), db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    username = payload.get("username")
    role_code = payload.get("role_code")
    if username is None or role_code is None or user_id is None:
        raise HTTPException(status_code=401, detail="Token 缺少标识")
    return schemas_auth.ValidateTokenUserItem(
        user_id=user_id, username=username, role_code=role_code
    )


def require_role(*roles: str):
    """角色权限依赖注入。用法: Depends(require_role("admin","analyst"))"""

    def role_checker(
        current_user: schemas_auth.ValidateTokenUserItem = Depends(get_current_user),
    ):
        if current_user.role_code not in roles and current_user.role_code != "admin":
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user

    return role_checker
