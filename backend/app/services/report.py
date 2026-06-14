"""报告查询与审核服务"""
import math
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.schemas import report as schemas_report
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.core.database import commit_or_rollback


async def get_report_list(db, request):
    """获取报告分页列表"""
    stmt = select(Report)
    if request.report_type:
        stmt = stmt.where(Report.report_type == request.report_type)
    if request.status:
        stmt = stmt.where(Report.status == request.status)
    if request.keyword:
        stmt = stmt.where(Report.title.like(f"%{request.keyword}%"))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    entities = (await db.scalars(
        stmt.order_by(Report.created_at.desc())
        .offset((request.page - 1) * request.page_size)
        .limit(request.page_size)
    )).all()

    return PaginatedResponse(
        lists=[schemas_report.GetReportListResponse.model_validate(e) for e in entities],
        pagination=PaginationInfo(
            page=request.page,
            page_size=request.page_size,
            total=total or 0,
            total_pages=math.ceil((total or 0) / request.page_size),
        ),
    )


async def get_report_detail(db, report_id):
    """获取报告详情"""
    entity = await db.get(Report, report_id)
    if not entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "报告不存在")
    return schemas_report.GetReportDetailResponse.model_validate(entity)


async def generate_report(db, request):
    """创建报告记录，返回 report_id（实际生成由路由层异步触发）"""
    now = datetime.now()
    entity = Report(
        title=f"{request.report_type}报告-{now.strftime('%Y%m%d')}",
        report_type=request.report_type,
        status="generating",
        period_start=now,
        period_end=now,
    )
    db.add(entity)
    await commit_or_rollback(db)
    await db.refresh(entity)
    return schemas_report.GenerateReportResponse(report_id=entity.id, status="generating")


async def review_report(db, report_id, request):
    """审核报告"""
    entity = await db.get(Report, report_id)
    if not entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "报告不存在")
    if request.action == "approve":
        entity.status = "published"
        entity.published_at = datetime.now()
    entity.review_comment = request.comment
    await commit_or_rollback(db)
    return schemas_report.ReviewReportResponse(success=True)


async def export_report(db, report_id):
    """导出报告内容"""
    entity = await db.get(Report, report_id)
    if not entity:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "报告不存在")
    lines = [f"# {entity.title}", "", entity.summary or ""]
    if entity.sections:
        for sec in entity.sections:
            lines.extend(["", f"## {sec.get('title', '')}", "", sec.get("content", "")])
    if entity.conclusion:
        lines.extend(["", "## 结论", "", entity.conclusion])
    return "\n".join(lines)
