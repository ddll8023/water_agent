"""图谱相关 Schema"""

from pydantic import BaseModel, ConfigDict, Field

# ========== 辅助类（Support）==========


class GetGraphOverviewNodeItem(BaseModel):
    """图谱节点"""

    id: str = Field(..., description="节点唯一标识（复合 ID）")
    name: str = Field(..., description="节点名称")
    type: str = Field(
        ...,
        description="节点类型（Reservoir/River/PollutionSource/Indicator/MonitoringStation）",
    )
    code: str | None = Field(None, description="节点编码")
    watershed: str | None = Field(None, description="所属流域")
    water_grade: str | None = Field(None, description="水质等级")
    risk_level: str | None = Field(None, description="风险等级")
    subtype: str | None = Field(None, description="子类型")

    model_config = ConfigDict(from_attributes=True)


class GetGraphOverviewEdgeItem(BaseModel):
    """图谱边"""

    source: str = Field(..., description="起始节点 ID")
    target: str = Field(..., description="目标节点 ID")
    relation: str = Field(..., description="关系类型")

    model_config = ConfigDict(from_attributes=True)


# ========== 请求类（Request）==========


class SearchNodeRequest(BaseModel):
    """搜索节点请求"""

    keyword: str = Field(..., description="搜索关键字")


# ========== 响应类（Response）==========


class GetNodeDetailResponse(BaseModel):
    """节点详情响应"""

    id: str = Field(..., description="节点唯一标识")
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型")
    attributes: dict[str, str | None] = Field(
        default_factory=dict, description="节点全部属性键值对"
    )

    model_config = ConfigDict(from_attributes=True)


class GetGraphOverviewResponse(BaseModel):
    """图谱全局概览响应"""

    nodes: list[GetGraphOverviewNodeItem] = Field(..., description="图谱节点列表")
    edges: list[GetGraphOverviewEdgeItem] = Field(..., description="图谱边列表")

    model_config = ConfigDict(from_attributes=True)


class GetGraphExpandResponse(BaseModel):
    """节点一跳扩展响应"""

    nodes: list[GetGraphOverviewNodeItem] = Field(
        default_factory=list, description="相邻节点列表"
    )
    edges: list[GetGraphOverviewEdgeItem] = Field(
        default_factory=list, description="相邻关系列表"
    )

    model_config = ConfigDict(from_attributes=True)


class SearchNodeResponse(BaseModel):
    """搜索节点响应"""

    node_list: list[GetGraphOverviewNodeItem] = Field(
        default_factory=list, description="节点列表"
    )

    model_config = ConfigDict(from_attributes=True)
