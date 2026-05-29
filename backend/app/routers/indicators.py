from fastapi import APIRouter, Depends, Query, Body, Path
from typing import Annotated

from sqlalchemy.sql.schema import Identity
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException

from app.core.security import get_current_user, require_role
from app.schemas import indicators as schemas_indicators
from app.services import indicators as service_indicators
import math

router = APIRouter(prefix="/api/indicators", tags=["指标模块"])


@router.post(
    "/create",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="创建指标",
)
async def create_indicator(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_indicator_request: Annotated[
        schemas_indicators.CreateIndicatorRequest, Body(..., description="创建指标请求")
    ],
):
    """创建指标"""
    try:
        return success(
            await service_indicators.create_indicator(db, create_indicator_request)
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/list",
    response_model=ApiResponse[
        PaginatedResponse[schemas_indicators.GetIndicatorListResponse]
    ],
    dependencies=[Depends(require_role("admin"))],
    description="获取指标列表",
)
async def get_indicator_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_indicator_list_request: Annotated[
        schemas_indicators.GetIndicatorListRequest,
        Body(..., description="获取指标列表请求"),
    ],
):
    """获取指标列表"""
    try:
        return success(
            await service_indicators.get_indicator_list(db, get_indicator_list_request)
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_indicators.GetIndicatorDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取指标详情",
)
async def get_indicator_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="指标ID")],
):
    """获取指标详情"""
    try:
        return success(await service_indicators.get_indicator_detail(db, id))
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="更新指标",
)
async def update_indicator(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="指标ID")],
    update_indicator_request: Annotated[
        schemas_indicators.UpdateIndicatorRequest, Body(..., description="更新指标请求")
    ],
):
    """更新指标"""
    try:
        return success(
            await service_indicators.update_indicator(db, id, update_indicator_request)
        )
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除指标",
)
async def delete_indicator(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="指标ID")],
):
    """删除指标"""
    try:
        return success(await service_indicators.delete_indicator(db, id))
    except ServiceException as e:
        return error(e.code, e.message)
