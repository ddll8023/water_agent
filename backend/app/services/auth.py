from app.schemas import auth as schemas_auth
from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import user as models_user
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
import bcrypt
from app.core.security import create_access_token
from sqlalchemy import select
from datetime import datetime

logger = setup_logger(__name__)


async def login(db: AsyncSession, login_request: schemas_auth.LoginRequest):
    """登录"""
    user_entity = await db.scalar(
        select(models_user.User).where(
            models_user.User.username == login_request.username,
            models_user.User.status == 1,
        )
    )
    if not user_entity:
        logger.error("用户不存在或已禁用")
        raise ServiceException(message="用户不存在或已禁用")

    if not bcrypt.checkpw(
        login_request.password.encode("utf-8"), user_entity.password.encode("utf-8")
    ):
        logger.error("密码错误")
        raise ServiceException(message="密码错误")

    user_entity.last_login = datetime.now()
    await commit_or_rollback(db)

    access_token = create_access_token(
        {
            "user_id": user_entity.id,
            "username": user_entity.username,
            "role_id": user_entity.role_id,
        }
    )
    return schemas_auth.LoginResponse(
        access_token=access_token,
        username=user_entity.username,
    )


async def register(db: AsyncSession, register_request: schemas_auth.RegisterRequest):
    """注册"""
    user_entity = await db.scalar(
        select(models_user.User).where(
            models_user.User.username == register_request.username,
        )
    )
    if user_entity:
        logger.error("用户名已存在")
        raise ServiceException(message="用户名已存在")

    user_entity = models_user.User(
        username=register_request.username,
        password=bcrypt.hashpw(
            register_request.password.encode("utf-8"), bcrypt.gensalt()
        ),
        phone=register_request.phone,
    )
    db.add(user_entity)
    await commit_or_rollback(db)
    return schemas_auth.RegisterResponse(
        user_id=user_entity.id,
        username=user_entity.username,
    )


async def logout():
    """退出登录"""
    return {"message": "退出登录成功"}


async def get_current_user_detail(
    db: AsyncSession, user_item: schemas_auth.ValidateTokenUserItem
):
    """获取当前用户详情"""
    user_entity = await db.get(models_user.User, user_item.user_id)
    if not user_entity:
        logger.error("用户不存在")
        raise ServiceException(message="用户不存在")
    role_entity = await db.get(models_user.Role, user_entity.role_id)
    if not role_entity:
        logger.error("角色不存在")
        raise ServiceException(message="角色不存在")

    return schemas_auth.GetCurrentUserDetailResponse(
        user_id=user_entity.id,
        username=user_entity.username,
        role=role_entity.name,
        phone=user_entity.phone,
        dingtalk_id=user_entity.dingtalk_id,
    )
