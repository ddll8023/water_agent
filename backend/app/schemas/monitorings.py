from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


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
