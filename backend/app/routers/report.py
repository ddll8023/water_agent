"""报告路由"""
from typing import Annotated
from fastapi import APIRouter, Depends, Body, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.response import success, error
from app.schemas import report as schemas_report
from app.services import report as services_report
from app.utils.exception import ServiceException
from app.pipelines.report_generator import background_generate

router = APIRouter(prefix="/api/v1/reports", tags=["报告中心"])


@router.post(
    "/list",
    response_model=ApiResponse[PaginatedResponse[schemas_report.GetReportListResponse]],
    dependencies=[Depends(require_role("admin", "user"))],
    description="获取报告列表",
)
async def get_report_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[schemas_report.GetReportListRequest, Body(...)],
):
    """获取报告列表"""
    try:
        result = await services_report.get_report_list(db, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/{id}",
    response_model=ApiResponse[schemas_report.GetReportDetailResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    description="获取报告详情",
)
async def get_report_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="报告ID")],
):
    """获取报告详情"""
    try:
        result = await services_report.get_report_detail(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/generate",
    response_model=ApiResponse[schemas_report.GenerateReportResponse],
    dependencies=[Depends(require_role("admin"))],
    description="生成报告（后台异步执行）",
)
async def generate_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Annotated[schemas_report.GenerateReportRequest, Body(...)],
    background_tasks: BackgroundTasks,
):
    """生成报告：创建记录后后台异步执行"""
    try:
        result = await services_report.generate_report(db, request)
        background_tasks.add_task(
            background_generate,
            result.report_id,
            request.report_type,
            request.reservoir_ids,
            request.alert_id,
        )
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/{id}/review",
    response_model=ApiResponse[schemas_report.ReviewReportResponse],
    dependencies=[Depends(require_role("admin"))],
    description="审核报告",
)
async def review_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="报告ID")],
    request: Annotated[schemas_report.ReviewReportRequest, Body(...)],
):
    """审核报告"""
    try:
        result = await services_report.review_report(db, id, request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.post(
    "/{id}/export",
    response_model=ApiResponse[str],
    dependencies=[Depends(require_role("admin", "user"))],
    description="导出报告",
)
async def export_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: Annotated[int, Path(..., description="报告ID")],
    body: Annotated[dict | None, Body(description="导出参数 {format: 'markdown'}")] = None,
):
    """导出报告为 markdown 文本"""
    try:
        result = await services_report.export_report(db, id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
