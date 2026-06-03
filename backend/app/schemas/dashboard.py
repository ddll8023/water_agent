from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


# ========== 辅助类（Support）==========


class ReservoirCardIndicatorItem(BaseModel):
    """水库卡片指标项"""

    name: str = Field(description="指标名称")
    code: str = Field(description="指标编码")
    value: str | None = Field(None, description="最新监测值")
    unit: str | None = Field(None, description="单位")


# ========== 请求类（Request）==========


# ========== 响应类（Response）==========


class ReservoirCardResponse(BaseModel):
    """水库卡片响应参数"""

    id: int = Field(description="水库ID")
    name: str = Field(description="水库名称")
    code: str = Field(description="水库编号")
    location: str | None = Field(None, description="所在位置")
    water_grade: str | None = Field(None, description="水质等级")
    watershed: str | None = Field(None, description="所属流域")
    station_count: int = Field(0, description="站点总数")
    online_station_count: int = Field(0, description="在线站点数")
    alert_count: int = Field(0, description="告警记录数")
    indicators: list[ReservoirCardIndicatorItem] = Field(
        default_factory=list, description="核心指标监测值"
    )

    model_config = ConfigDict(from_attributes=True)


class GetDashboardOverviewResponse(BaseModel):
    """获取仪表盘总览响应参数"""

    reservoir_count: int = Field(0, description="水库总数")
    normal_count: int = Field(0, description="正常站点数")
    abnormal_count: int = Field(0, description="异常站点数")
    alert_count: int = Field(0, description="告警总数")
    offline_stations: int = Field(0, description="离线站点数")

    model_config = ConfigDict(from_attributes=True)


class GetLastAlertResponse(BaseModel):
    """获取最近5条告警记录响应参数"""

    alert_id: int = Field(alias="id", description="告警ID")
    reservoir_id: int = Field(description="水库ID")
    title: str = Field(description="告警标题")
    alert_level: int = Field(description="告警等级：1=info 2=warning 3=critical")
    indicators: list[dict] = Field(
        default_factory=list,
        description="超标指标列表_name_value_limit",
    )
    status: int = Field(description="状态_0=待确认_1=已确认_2=处置中_3=已解决")
    detected_at: datetime = Field(description="检出时间")

    model_config = ConfigDict(from_attributes=True)
