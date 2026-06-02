from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class GetAlertListRequest(BaseModel):
    """获取预警列表请求参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")
    reservoir_id: int | None = Field(None, description="水库ID")
    alert_level: str | None = Field(None, description="预警等级：info/warning/critical")
    status: str | None = Field(None, description="状态：new/confirmed/processing/resolved")
    start_time: datetime | None = Field(None, description="检出开始时间")
    end_time: datetime | None = Field(None, description="检出结束时间")


class GetAlertListResponse(BaseModel):
    """获取预警列表响应参数"""

    id: int = Field(description="预警ID")
    reservoir_id: int = Field(description="水库ID")
    handler_id: int | None = Field(None, description="处理人ID")
    title: str = Field(description="预警标题")
    alert_level: str = Field(description="预警等级")
    indicators: list | None = Field(None, description="超标指标列表")
    source_desc: str | None = Field(None, description="溯源描述")
    suggestion: str | None = Field(None, description="处置建议")
    status: str = Field(description="状态")
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)
