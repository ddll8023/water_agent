from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


# ========== 辅助类（Support）==========


class CachedRecordItem(BaseModel):
    """采集缓存记录项（待写入 Redis）"""

    reservoir_id: int = Field(description="水库ID")
    indicator_id: int = Field(description="指标ID")
    indicator_name: str = Field(description="指标名称")
    value: float = Field(description="监测值")
    record_time: datetime = Field(description="监测时间")

    model_config = ConfigDict(from_attributes=True)

class GetMonitoringRecordsTrendResponseItem(BaseModel):
    """获取监测记录趋势响应参数项"""

    reservoir_id: int = Field(description="水库ID")
    indicator_id: int = Field(description="指标ID")
    record_time: datetime = Field(description="监测时间")
    value: float = Field(description="监测值")

    model_config = ConfigDict(from_attributes=True)


class IndicatorLatestValueItem(BaseModel):
    """指标最新值项"""

    indicator_id: int = Field(description="指标ID")
    indicator_name: str = Field(description="指标名称")
    value: float = Field(description="最新监测值")
    quality_flag: Literal[0, 1, 2] = Field(description="数据质量标志：0 可疑，1 正常，2 无效")
    record_time: datetime = Field(description="监测时间")

    model_config = ConfigDict(from_attributes=True)


# ========== 请求类（Request）==========

class GetMonitoringRecordsListRequest(BaseModel):
    """获取监测记录列表请求参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")
    reservoir_id: int | None = Field(None, description="水库ID")
    station_id: int | None = Field(None, description="站点ID")
    indicator_id: int | None = Field(None, description="指标ID")
    start_time: datetime | None = Field(
        None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"
    )
    end_time: datetime | None = Field(
        None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS"
    )
    quality_flag: Literal[0, 1, 2, None] = Field(
        None, description="数据质量标志：0 可疑，1 正常，2 无效"
    )


class GetLastMonitoringRecordRequest(BaseModel):
    """获取最新监测记录请求参数"""

    reservoir_id: int = Field(description="水库ID")
    station_id: int = Field(description="站点ID")
    indicator_id: int = Field(description="指标ID")


class GetReservoirLatestIndicatorsRequest(BaseModel):
    """获取水库各指标最新值请求参数"""

    reservoir_id: int = Field(description="水库ID")


class ManualInputRequest(BaseModel):
    """人工采样录入请求"""

    station_id: int = Field(..., description="站点ID")
    indicator_id: int = Field(..., description="指标ID")
    value: float = Field(..., gt=-999999, lt=999999, description="监测值")
    record_time: datetime = Field(..., description="监测时间")
    quality_flag: int | None = Field(1, description="数据质量：0可疑 1正常 2无效")


class GetMonitoringRecordsTrendRequest(BaseModel):
    """获取监测记录趋势请求参数"""

    reservoir_id: int = Field(description="水库ID")
    indicator_id: int = Field(description="指标ID")
    start_time: datetime | None = Field(
        None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"
    )
    end_time: datetime | None = Field(
        None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS"
    )


# ========== 响应类（Response）==========

class GetMonitoringRecordsListResponse(BaseModel):
    """获取监测记录列表响应参数"""

    id: int = Field(description="监测记录ID")
    reservoir_id: int = Field(description="水库ID")
    station_id: int = Field(description="站点ID")
    indicator_id: int = Field(description="指标ID")
    value: float = Field(description="监测值")
    record_time: datetime = Field(description="监测时间")

    model_config = ConfigDict(from_attributes=True)


class GetLastMonitoringRecordResponse(BaseModel):
    """获取最新监测记录响应参数"""

    id: int = Field(description="监测记录ID")
    reservoir_id: int = Field(description="水库ID")
    station_id: int = Field(description="站点ID")
    indicator_id: int = Field(description="指标ID")
    value: float = Field(description="监测值")
    quality_flag: Literal[0, 1, 2] = Field(description="数据质量标志")
    record_time: datetime = Field(description="监测时间")

    model_config = ConfigDict(from_attributes=True)


class GetReservoirLatestIndicatorsResponse(BaseModel):
    """获取水库各指标最新值响应参数"""

    reservoir_id: int = Field(description="水库ID")
    records: list[IndicatorLatestValueItem] = Field(description="各指标最新监测值列表")


class GetMonitoringRecordsTrendResponse(BaseModel):
    """获取监测记录趋势响应参数"""

    lists: list[GetMonitoringRecordsTrendResponseItem] = Field(
        default_factory=list, description="监测记录趋势列表"
    )
    total: int = Field(0, description="总记录数")
