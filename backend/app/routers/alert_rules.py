from typing import Annotated
from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.response import success, error
from app.schemas import alert_rules as schemas_alert_rules
from app.services import alert_rules as services_alert_rules
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/alert-rules", tags=["预警规则管理"])


@router.post(
    "/list",
    response_model=ApiResponse[PaginatedResponse[schemas_alert_rules.GetAlertRuleListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取预警规则列表",
)
async def get_alert_rule_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[
        schemas_alert_rules.GetAlertRuleListRequest,
        Body(..., description="获取预警规则列表请求"),
    ],
):
    """获取预警规则列表"""
    try:
        result = await services_alert_rules.get_alert_rule_list(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/{id}",
    response_model=ApiResponse[schemas_alert_rules.GetAlertRuleDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取预警规则详情",
)
async def get_alert_rule_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="规则ID")],
):
    """获取预警规则详情"""
    try:
        result = await services_alert_rules.get_alert_rule_detail(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/create",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="创建预警规则",
)
async def create_alert_rule(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[
        schemas_alert_rules.CreateAlertRuleRequest,
        Body(..., description="创建预警规则请求"),
    ],
):
    """创建预警规则"""
    try:
        result = await services_alert_rules.create_alert_rule(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.put(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="更新预警规则",
)
async def update_alert_rule(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="规则ID")],
    request: Annotated[
        schemas_alert_rules.UpdateAlertRuleRequest,
        Body(..., description="更新预警规则请求"),
    ],
):
    """更新预警规则"""
    try:
        result = await services_alert_rules.update_alert_rule(db, id, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.delete(
    "/{id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除预警规则",
)
async def delete_alert_rule(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="规则ID")],
):
    """删除预警规则"""
    try:
        result = await services_alert_rules.delete_alert_rule(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
