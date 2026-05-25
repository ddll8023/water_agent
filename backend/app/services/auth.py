from app.schemas import user as schemas_user
from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import user as models_user
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
import bcrypt
from app.core.security import create_access_token

logger = setup_logger(__name__)


async def login(db: AsyncSession, login_request: schemas_user.LoginRequest):
    """登录"""
    user_entity = await db.scalar(
        models_user.User.select().where(
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

    access_token = create_access_token(
        {
            "user_id": user_entity.id,
            "username": user_entity.username,
            "role_id": user_entity.role_id,
        }
    )
    return schemas_user.LoginResponse(
        access_token=access_token,
        username=user_entity.username,
    )


async def register(db: AsyncSession, register_request: schemas_user.RegisterRequest):
    """注册"""
    user_entity = await db.scalar(
        models_user.User.select().where(
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
    await db.add(user_entity)
    commit_or_rollback(db)
    return schemas_user.RegisterResponse(
        user_id=user_entity.id,
        username=user_entity.username,
        role=user_entity.role.name,
    )
