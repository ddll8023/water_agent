from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from app.schemas import graph as schemas_graph

# ========== 辅助类（Support）==========


class AlertNoteItem(BaseModel):
    """处置备注条目（嵌入 AlertEvent.notes JSON 数组）"""

    id: int = Field(description="备注ID")
    user_id: int | None = Field(None, description="创建人ID")
    content: str = Field(description="备注内容")
    created_at: datetime = Field(description="创建时间")


class AlertDetailItem(BaseModel):
    """预警详情"""

    id: int = Field(description="预警ID")
    reservoir_id: int = Field(description="水库ID")
    title: str = Field(description="预警标题")
    alert_level: int = Field(description="预警等级：1=info 2=warning 3=critical")
    indicators: list[dict] | None = Field(
        None, description="超标指标列表_name_value_limit"
    )
    source_desc: str | None = Field(None, description="溯源描述")
    source: int | None = Field(None, description="来源：0=规则判定 1=Agent趋势分析")
    suggestion: str | None = Field(None, description="处置建议")
    notes: list[AlertNoteItem] | None = Field(
        default_factory=list, description="处置备注列表"
    )
    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")

    model_config = ConfigDict(from_attributes=True)


class SuggestionPromptInputItem(BaseModel):
    """AI 建议提示词输入"""

    reservoir_name: str = Field("未知", description="水库名称")
    reservoir_code: str = Field("未知", description="水库编号")
    reservoir_location: str = Field("未知", description="水库所在位置")
    watershed: str = Field("未知", description="所属流域")
    capacity: str = Field("未知", description="库容")
    water_grade: str = Field("未知", description="当前水质等级")
    alert_level: int = Field(description="预警等级：1=info 2=warning 3=critical")
    detected_at: datetime = Field(description="检出时间")
    source_desc: str = Field("暂无", description="溯源信息描述")
    indicators_text: str = Field(description="超标指标文本")
    rag_content_section: str = Field(
        "（未检索到相关知识库内容）", description="知识库检索参考内容"
    )

    model_config = ConfigDict(from_attributes=True)


class LLMSuggestionItem(BaseModel):
    """ai生成建议步骤内容"""

    step: int = Field(..., ge=1, description="序号")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="详细说明")

    model_config = ConfigDict(from_attributes=True)


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
    alert_level: int | None = Field(
        None, description="预警等级：1=info 2=warning 3=critical"
    )
    status: int | None = Field(
        None, description="状态：0=待确认/1=已确认/2=处置中/3=已解决"
    )
    source: int | None = Field(None, description="来源：0=规则判定 1=Agent趋势分析")
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
    source: int | None = Field(None, description="来源：0=规则判定 1=Agent趋势分析")
    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    suggestion_status: int = Field(
        default=0, description="建议状态：0=无 1=生成中 2=已生成 3=已确认"
    )
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("suggestion_status", mode="before")
    @classmethod
    def coerce_suggestion_status(cls, v):
        return 0 if v is None else v


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
    source: int | None = Field(None, description="来源：0=规则判定 1=Agent趋势分析")
    suggestion: list[dict] | None = Field(default=None, description="处置建议")
    suggestion_status: int = Field(
        default=0, description="建议状态：0=无 1=生成中 2=已生成 3=已确认"
    )
    notes: list[AlertNoteItem] | None = Field(
        default_factory=list, description="处置备注列表"
    )
    status: int = Field(description="状态：0=待确认/1=已确认/2=处置中/3=已解决")
    detected_at: datetime = Field(description="检出时间")
    resolved_at: datetime | None = Field(None, description="解决时间")

    model_config = ConfigDict(from_attributes=True)


class GetTracePollutionResponse(BaseModel):
    """溯源响应"""

    nodes: list[schemas_graph.GetGraphOverviewNodeItem] = Field(
        default_factory=list, description="节点"
    )
    edges: list[schemas_graph.GetGraphOverviewEdgeItem] = Field(
        default_factory=list, description="边"
    )
    sources: list[schemas_graph.TraceSourceItem] = Field(
        default_factory=list, description="来源"
    )


class LLMSuggestionResponse(BaseModel):
    """ai生成建议响应"""

    lists: list[LLMSuggestionItem] = Field(default_factory=list, description="步骤列表")


class SimilarEventItem(GetAlertListResponse):
    """历史相似事件项"""

    matched_indicators: list[str] = Field(
        default_factory=list, description="与本预警匹配的指标名称列表"
    )
