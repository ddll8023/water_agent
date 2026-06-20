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

    stmt = select(models_user.User)

    if get_user_list_request.keyword:
        stmt = stmt.where(
            models_user.User.username.like(f"%{get_user_list_request.keyword}%")
        )
    if get_user_list_request.role_id:
        stmt = stmt.where(models_user.User.role_id == get_user_list_request.role_id)
    if get_user_list_request.status is not None:
        stmt = stmt.where(models_user.User.status == get_user_list_request.status)

    user_entity_list = await db.scalars(
        stmt.order_by(models_user.User.id.desc())
        .offset((get_user_list_request.page - 1) * get_user_list_request.page_size)
        .limit(get_user_list_request.page_size)
    )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    return PaginatedResponse(
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


async def get_user_detail(db: AsyncSession, id: int):
    """获取用户详情"""
    user_entity = await db.get(models_user.User, id)
    if not user_entity:
        raise ServiceException("用户不存在")
    return schemas_users.GetUserDetailResponse.model_validate(user_entity)


async def update_user(
    db: AsyncSession, id: int, update_user_request: schemas_users.UpdateUserRequest
):
    """更新用户"""
    user_entity = await db.get(models_user.User, id)
    if not user_entity:
        raise ServiceException("用户不存在")

    if update_user_request.real_name:
        user_entity.real_name = update_user_request.real_name
    if update_user_request.phone:
        user_entity.phone = update_user_request.phone
    if update_user_request.role_id:
        user_entity.role_id = update_user_request.role_id
    if update_user_request.dingtalk_id:
        user_entity.dingtalk_id = update_user_request.dingtalk_id
    if update_user_request.status:
        user_entity.status = update_user_request.status

    await commit_or_rollback(db)
    return schemas_users.UpdateUserResponse.model_validate(user_entity)


async def reset_password(
    db: AsyncSession,
    id: int,
    reset_password_request: schemas_users.ResetPasswordRequest,
):
    """重置密码"""
    user_entity = await db.get(models_user.User, id)
    if not user_entity:
        raise ServiceException("用户不存在")

    user_entity.password = hashpw(
        reset_password_request.password.encode("utf-8"), gensalt()
    )
    await commit_or_rollback(db)
    return True
