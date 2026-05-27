from fastapi import APIRouter, Depends, Query, Body, Path
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import reservoir as schemas_reservoir
from app.services import reservoir as service_reservoir
import math

router = APIRouter(prefix="/api/reservoir", tags=["水库管理"])


@router.get(
    "/list",
    response_model=ApiResponse[
        PaginatedResponse[schemas_reservoir.GetReservoirListResponse]
    ],
    dependencies=[Depends(require_role("admin"))],
    description="获取水库列表，分页返回",
)
async def get_reservoir_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_reservoir_list_request: Annotated[
        schemas_reservoir.GetReservoirListRequest,
        Query(..., description="分页请求参数"),
    ],
):
    try:
        result = await service_reservoir.get_reservoir_list(
            db, get_reservoir_list_request
        )
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/create",
    response_model=ApiResponse,
    dependencies=[Depends(require_role("admin"))],
    description="创建水库",
)
async def create_reservoir(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_reservoir_request: Annotated[
        schemas_reservoir.CreateReservoirRequest,
        Body(..., description="创建水库请求参数"),
    ],
):
    try:
        return success(
            await service_reservoir.create_reservoir(db, create_reservoir_request)
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_reservoir.GetReservoirDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取水库详情",
)
async def get_reservoir_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="水库ID")],
):
    try:
        return success(await service_reservoir.get_reservoir_detail(db, id))
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_role("admin"))],
    description="更新水库",
)
async def update_reservoir(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="水库ID")],
    update_reservoir_request: Annotated[
        schemas_reservoir.UpdateReservoirRequest,
        Body(..., description="更新水库请求参数"),
    ],
):
    try:
        return success(
            await service_reservoir.update_reservoir(db, id, update_reservoir_request)
        )
    except ServiceException as e:
        return error(e.code, e.message)
