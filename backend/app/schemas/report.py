"""报告相关 Schema 定义"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ========== 辅助类（Support）==========

class ReportPromptItem(BaseModel):
    """报告生成 prompt 变量集合"""

    period_start: str = Field(default="", description="覆盖起始时间")
    period_end: str = Field(default="", description="覆盖结束时间")
    patrol_summary: dict | None = Field(default=None, description="巡检执行统计")
    alert_stats: dict | None = Field(default=None, description="预警事件统计")
    indicator_stats: list | None = Field(default=None, description="核心指标各水库均值")
    analysis_reference: list | None = Field(default=None, description="分析摘要列表")
    monthly_trend: list | None = Field(default=None, description="月度预警趋势")
    period_comparison: dict | None = Field(default=None, description="季度同比对比")
    alert_title: str = Field(default="", description="预警标题")
    alert_level: str = Field(default="", description="预警等级")
    detected_at: str = Field(default="", description="检出时间")
    alert_status: str = Field(default="", description="预警状态")
    indicators_detail: list | None = Field(default=None, description="超标指标详情")
    trace_info: str = Field(default="", description="溯源信息(JSON)")
    suggestion_detail: list | None = Field(default=None, description="AI处置建议")
    process_detail: str = Field(default="", description="处置过程(JSON)")


# ========== 请求类（Request）==========

class GetReportListRequest(BaseModel):
    """获取报告列表请求"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=12, ge=1, le=100, description="每页记录数")
    report_type: str | None = Field(None, description="报告类型: daily/quarterly/event")
    status: str | None = Field(None, description="状态: draft/published/no_data")
    keyword: str | None = Field(None, description="标题关键词")


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    report_type: str = Field(..., description="报告类型: daily/quarterly/event")
    reservoir_ids: list[int] | None = Field(None, description="水库ID列表")
    alert_id: int | None = Field(None, description="预警ID（事件报告时必传）")


class ReviewReportRequest(BaseModel):
    """审核报告请求"""
    action: str = Field(..., description="审核动作: approve/reject")
    comment: str | None = Field(None, description="审核备注")


# ========== 响应类（Response）==========

class GetReportListResponse(BaseModel):
    """报告列表项响应"""
    id: int = Field(description="报告ID")
    title: str = Field(description="报告标题")
    report_type: str = Field(description="报告类型")
    status: str = Field(description="状态")
    summary: str | None = Field(None, description="摘要")
    created_at: datetime | None = Field(None, description="创建时间")
    published_at: datetime | None = Field(None, description="发布时间")
    model_config = ConfigDict(from_attributes=True)


class GetReportDetailResponse(BaseModel):
    """报告详情响应"""
    id: int = Field(description="报告ID")
    title: str = Field(description="报告标题")
    report_type: str = Field(description="报告类型")
    status: str = Field(description="状态")
    summary: str | None = Field(None, description="AI 生成摘要")
    sections: list | None = Field(None, description="结构化章节 [{title, content}]")
    conclusion: str | None = Field(None, description="总体结论与建议")
    period_start: datetime | None = Field(None, description="覆盖起始时间")
    period_end: datetime | None = Field(None, description="覆盖结束时间")
    generated_by: int | None = Field(None, description="生成人ID")
    reviewed_by: int | None = Field(None, description="审核人ID")
    review_comment: str | None = Field(None, description="审核意见")
    published_at: datetime | None = Field(None, description="发布时间")
    created_at: datetime | None = Field(None, description="创建时间")
    model_config = ConfigDict(from_attributes=True)


class GenerateReportResponse(BaseModel):
    """生成报告响应"""
    report_id: int = Field(description="报告ID")
    status: str = Field(description="任务状态: generating")


class ReviewReportResponse(BaseModel):
    """审核报告响应"""
    success: bool = Field(description="操作是否成功")
