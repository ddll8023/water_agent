from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import role as models_role
from app.schemas.common import PaginatedResponse, PaginationInfo
from app.schemas import roles as schemas_roles
import math


async def get_role_list(
    db: AsyncSession, get_role_list_request: schemas_roles.GetRoleListRequest
):
    """获取角色列表"""
    total = await db.scalar(select(func.count(models_role.Role.id)))

    role_entity_list = await db.scalars(
        select(models_role.Role)
        .offset((get_role_list_request.page - 1) * get_role_list_request.page_size)
        .limit(get_role_list_request.page_size)
    )

    return PaginatedResponse[schemas_roles.GetRoleListResponse](
        lists=[
            schemas_roles.GetRoleListResponse.model_validate(role_entity)
            for role_entity in role_entity_list
        ],
        pagination=PaginationInfo(
            total=total,
            total_pages=math.ceil(total / get_role_list_request.page_size),
            page=get_role_list_request.page,
            page_size=get_role_list_request.page_size,
        ),
    )


async def add_role(db: AsyncSession, add_role_request: schemas_roles.AddRoleRequest):
    """添加角色"""
    role_entity = await db.scalar(
        select(models_role.Role).where(
            models_role.Role.code == add_role_request.code
            or models_role.Role.name == add_role_request.name
        )
    )
    if role_entity:
        raise ServiceException("角色编码或名称已存在")
    role_entity = models_role.Role(**add_role_request.model_dump())
    db.add(role_entity)
    await commit_or_rollback(db)
    await db.refresh(role_entity)
    return schemas_roles.AddRoleResponse.model_validate(role_entity)
