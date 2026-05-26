from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import user as models_user
from app.schemas.common import PaginatedResponse, PaginationInfo
from app.schemas import users as schemas_users
import math
from bcrypt import hashpw, gensalt


async def get_user_list(
    db: AsyncSession, get_user_list_request: schemas_users.GetUserListRequest
):
    """获取用户列表"""
    total = await db.scalar(select(func.count(models_user.User.id)))

    user_entity_list = await db.scalars(
        select(models_user.User)
        .order_by(models_user.User.id.desc())
        .offset((get_user_list_request.page - 1) * get_user_list_request.page_size)
        .limit(get_user_list_request.page_size)
    )

    return PaginatedResponse[schemas_users.GetUserListResponse](
        lists=[
            schemas_users.GetUserListResponse.model_validate(user_entity)
            for user_entity in user_entity_list
        ],
        pagination=PaginationInfo(
            page=get_user_list_request.page,
            page_size=get_user_list_request.page_size,
            total=total,
            total_pages=math.ceil(total / get_user_list_request.page_size),
        ),
    )


async def add_user(db: AsyncSession, add_user_request: schemas_users.AddUserRequest):
    """添加用户"""
    user_entity = await db.scalar(
        select(models_user.User).where(
            models_user.User.username == add_user_request.username
        )
    )
    if user_entity:
        raise ServiceException("用户名已存在")

    user_entity = models_user.User(
        username=add_user_request.username,
        password=hashpw(add_user_request.password.encode("utf-8"), gensalt()),
        real_name=add_user_request.real_name,
        phone=add_user_request.phone,
        role_id=add_user_request.role_id,
        dingtalk_id=add_user_request.dingtalk_id,
    )

    db.add(user_entity)
    await commit_or_rollback(db)
    return schemas_users.AddUserResponse(
        id=user_entity.id,
        username=user_entity.username,
    )
