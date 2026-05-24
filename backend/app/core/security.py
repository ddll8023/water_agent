from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from fastapi import Depends, HTTPException, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timezone
from app.core.database import get_db

# Bearer token 方案
oahth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str):
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )


def get_current_user(
    token: str = Depends(oahth2_scheme), db: Session = Depends(get_db)
):
    payload = verify_token(token)
    username = payload["username"]
    if not username:
        raise HTTPException(status_code=401, detail="Token 缺少标识")
    user = db.query(SysUser).filter(SysUser.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
