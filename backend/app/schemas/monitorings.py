from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ========== 辅助类（Support）==========


class MockRtuIndicatorItem(BaseModel):
    """模拟 RTU 单指标数据项"""

    indicator_code: str = Field(..., description="指标编码")
    indicator_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="模拟值")
    unit: str = Field(..., description="单位")

    model_config = ConfigDict(from_attributes=True)


# ========== 请求类（Request）==========


class GetMockMonitoringRecordRequest(BaseModel):
    """获取模拟监测记录请求参数"""

    station_id: int = Field(..., description="站点ID")
    record_time_start: datetime | None = Field(None, description="监测时间开始")
    record_time_end: datetime | None = Field(None, description="监测时间结束")


# ========== 响应类（Response）==========


class MockRtuDataResponse(BaseModel):
    """模拟 RTU 数据响应"""

    station_id: int = Field(..., description="站点ID")
    station_code: str = Field(..., description="站点编号")
    reservoir_id: int = Field(..., description="水库ID")
    reservoir_name: str = Field(..., description="水库名称")
    record_time: datetime = Field(..., description="数据时间")
    indicators: list[MockRtuIndicatorItem] = Field(..., description="8个核心指标列表")
    water_grade: str = Field(..., description="水质等级")

    model_config = ConfigDict(from_attributes=True)
