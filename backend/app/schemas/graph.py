"""图谱相关 Schema"""
from pydantic import BaseModel, ConfigDict


# ========== 辅助类（Support）==========


class GetGraphOverviewNodeItem(BaseModel):
    """图谱节点"""
    id: str
    name: str
    type: str
    code: str | None = None
    watershed: str | None = None
    water_grade: str | None = None
    risk_level: str | None = None
    subtype: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GetGraphOverviewEdgeItem(BaseModel):
    """图谱边"""
    source: str
    target: str
    relation: str

    model_config = ConfigDict(from_attributes=True)


# ========== 响应类（Response）==========


class GetGraphOverviewResponse(BaseModel):
    """图谱全局概览响应"""
    nodes: list[GetGraphOverviewNodeItem]
    edges: list[GetGraphOverviewEdgeItem]

    model_config = ConfigDict(from_attributes=True)
