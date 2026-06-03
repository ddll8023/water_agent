from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select, or_
from app.models import role as models_role
from app.schemas.common import PaginatedResponse, PaginationInfo
from app.schemas import roles as schemas_roles
import math


async def get_role_list(
    db: AsyncSession, get_role_list_request: schemas_roles.GetRoleListRequest
):
    """获取角色列表"""

    stmt = select(models_role.Role)
    if get_role_list_request.keyword:
        stmt = stmt.where(
            models_role.Role.name.ilike(f"%{get_role_list_request.keyword}%")
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    role_entity_list = await db.scalars(
        stmt.order_by(models_role.Role.id.desc())
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
            or_(
                models_role.Role.code == add_role_request.code,
                models_role.Role.name == add_role_request.name,
            )
        )
    )
    if role_entity:
        raise ServiceException("角色编码或名称已存在")
    role_entity = models_role.Role(**add_role_request.model_dump())
    db.add(role_entity)
    await commit_or_rollback(db)
    await db.refresh(role_entity)
    return schemas_roles.AddRoleResponse.model_validate(role_entity)


async def get_role_detail(db: AsyncSession, role_id: int):
    """获取角色详情"""
    role_entity = await db.get(models_role.Role, role_id)
    if not role_entity:
        raise ServiceException("角色不存在")
    return schemas_roles.GetRoleDetailResponse.model_validate(role_entity)


async def update_role(
    db: AsyncSession, update_role_request: schemas_roles.UpateRoleRequest
):
    """更新角色"""
    role_entity = await db.get(models_role.Role, update_role_request.id)
    if not role_entity:
        raise ServiceException("角色不存在")
    if update_role_request.name is not None:
        role_entity.name = update_role_request.name
    if update_role_request.code is not None:
        role_entity.code = update_role_request.code
    if update_role_request.permissions is not None:
        role_entity.permissions = update_role_request.permissions
    await commit_or_rollback(db)
    await db.refresh(role_entity)
    return True


async def delete_role(db: AsyncSession, role_id: int):
    """删除角色"""
    role_entity = await db.get(models_role.Role, role_id)
    if not role_entity:
        raise ServiceException("角色不存在")
    await db.delete(role_entity)
    await commit_or_rollback(db)
    return True
