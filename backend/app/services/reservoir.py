from app.core.database import get_db, commit_or_rollback
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger_config import setup_logger
from app.utils.exception import ServiceException
from sqlalchemy import func, select
from app.models import role as models_role
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.schemas import roles as schemas_roles
import math
from app.models import reservoir as models_reservoir
from app.schemas import reservoir as schemas_reservoir
from app.utils.exception import ServiceException


async def get_reservoir_list(
    db: AsyncSession,
    get_reservoir_list_request: schemas_reservoir.GetReservoirListRequest,
):
    """获取水库列表"""
    total = await db.scalar(select(func.count(models_reservoir.Reservoir.id)))
    stmt = select(models_reservoir.Reservoir)
    if get_reservoir_list_request.keyword:
        stmt = stmt.where(
            models_reservoir.Reservoir.name.ilike(
                f"%{get_reservoir_list_request.keyword}%"
            )
        )
    if get_reservoir_list_request.watershed:
        stmt = stmt.where(
            models_reservoir.Reservoir.watershed == get_reservoir_list_request.watershed
        )
    if get_reservoir_list_request.water_grade:
        stmt = stmt.where(
            models_reservoir.Reservoir.water_grade
            == get_reservoir_list_request.water_grade
        )
    if get_reservoir_list_request.status is not None:
        stmt = stmt.where(
            models_reservoir.Reservoir.status == get_reservoir_list_request.status
        )
    reservoir_entity_list = await db.scalars(
        stmt.order_by(models_reservoir.Reservoir.id.desc())
        .offset(
            (get_reservoir_list_request.page - 1) * get_reservoir_list_request.page_size
        )
        .limit(get_reservoir_list_request.page_size)
    )

    return PaginatedResponse(
        lists=[
            schemas_reservoir.GetReservoirListResponse.model_validate(reservoir_entity)
            for reservoir_entity in reservoir_entity_list
        ],
        PaginationInfo=PaginationInfo(
            total=total,
            total_pages=math.ceil(total / get_reservoir_list_request.page_size),
            page=get_reservoir_list_request.page,
            page_size=get_reservoir_list_request.page_size,
        ),
    )


async def create_reservoir(
    db: AsyncSession, create_reservoir_request: schemas_reservoir.CreateReservoirRequest
):
    """创建水库"""
    existing = await db.scalar(
        select(models_reservoir.Reservoir).where(
            models_reservoir.Reservoir.code == create_reservoir_request.code
        )
    )
    if existing:
        raise ServiceException(ErrorCode.RESOURCE_ALREADY_EXISTS, "水库已存在")

    reservoir_entity = models_reservoir.Reservoir(
        **create_reservoir_request.model_dump()
    )
    db.add(reservoir_entity)
    await commit_or_rollback(db)
    await db.refresh(reservoir_entity)
    return True
