from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


class GetDashboardOverviewResponse(BaseModel):
    """获取仪表盘总览响应参数"""

    reservoir_count: int = Field(0, description="水库总数")
    normal_count: int = Field(0, description="正常站点数")
    abnormal_count: int = Field(0, description="异常站点数")
    alert_count: int = Field(0, description="告警总数")
    offline_stations: int = Field(0, description="离线站点数")

    model_config = ConfigDict(from_attributes=True)
