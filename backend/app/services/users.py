from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import user as models_user
from app.schemas.common import PaginatedResponse, PaginationInfo
from app.schemas import users as schemas_users
import math


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
