from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ========== 辅助类（Support）==========

class AlertNoteItem(BaseModel):
    """处置备注条目（嵌入 AlertEvent.notes JSON 数组）"""

    id: int = Field(description="备注ID")
    user_id: int | None = Field(None, description="创建人ID")
    content: str = Field(description="备注内容")
    created_at: datetime = Field(description="创建时间")


# ========== 请求类（Request）==========

class AddAlertNoteRequest(BaseModel):
    """添加处置备注请求参数"""

    content: str = Field(..., min_length=1, description="备注内容")


class BatchReadAlertsRequest(BaseModel):
    """批量标记已读请求参数"""

    ids: list[int] = Field(..., min_length=1, description="预警ID列表")
    handler_id: int | None = Field(None, description="处理人ID")


class GetAlertListRequest(BaseModel):
    """获取预警列表请求参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")
    reservoir_id: int | None = Field(None, description="水库ID")
    alert_level: int | None = Field(None, description="预警等级：1=info 2=warning 3=critical")
    status: int | None = Field(
        None, description="状态：0=待确认/1=已确认/2=处置中/3=已解决"
    )
    start_time: datetime | None = Field(None, description="检出开始时间")
    end_time: datetime | None = Field(None, description="检出结束时间")


class UpdateAlertRequest(BaseModel):
    """更新预警请求参数"""

    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    handler_id: int | None = Field(None, description="处理人ID")


# ========== 响应类（Response）==========

class GetUnreadCountResponse(BaseModel):
    """未读预警数响应参数"""

    count: int = Field(description="未读预警数（status=0）")

    model_config = ConfigDict(from_attributes=True)


class AlertNoteResponse(BaseModel):
    """处置备注响应参数（与 AlertNoteItem 结构一致）"""

    id: int = Field(description="备注ID")
    user_id: int | None = Field(None, description="创建人ID")
    content: str = Field(description="备注内容")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class GetAlertListResponse(BaseModel):
    """获取预警列表响应参数"""

    id: int = Field(description="预警ID")
    reservoir_id: int = Field(description="水库ID")
    handler_name: str | None = Field(None, description="处理人姓名")
    title: str = Field(description="预警标题")
    alert_level: int = Field(description="预警等级：1=info 2=warning 3=critical")
    indicators: list[dict] | None = Field(
        None, description="超标指标列表_name_value_limit"
    )
    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")

    model_config = ConfigDict(from_attributes=True)


class GetAlertDetailResponse(BaseModel):
    """获取预警详情响应参数"""

    id: int = Field(description="预警ID")
    reservoir_id: int = Field(description="水库ID")
    title: str = Field(description="预警标题")
    alert_level: int = Field(description="预警等级：1=info 2=warning 3=critical")
    indicators: list[dict] | None = Field(
        None, description="超标指标列表_name_value_limit"
    )
    source_desc: str | None = Field(None, description="溯源描述")
    suggestion: str | None = Field(None, description="处置建议")
    notes: list[AlertNoteItem] | None = Field(
        default_factory=list, description="处置备注列表"
    )
    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")

    model_config = ConfigDict(from_attributes=True)
