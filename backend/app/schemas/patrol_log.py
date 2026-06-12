from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class GetPatrolLogListRequest(BaseModel):
    """获取巡检日志列表请求"""

    status: int | None = Field(None, description="执行状态筛选")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")


class GetPatrolLogListResponse(BaseModel):
    """巡检日志列表响应"""

    id: int = Field(description="日志ID")
    executed_at: datetime = Field(description="执行开始时间")
    status: int = Field(description="执行状态_0=成功_1=部分失败_2=失败_3=无数据")
    station_count: int = Field(description="在线站点数")
    record_count: int = Field(description="入库记录数")
    new_alert_count: int = Field(description="新增预警数")
    merge_count: int = Field(description="合并预警数")
    duration_ms: int = Field(description="执行耗时_毫秒")
    error: str | None = Field(None, description="错误信息")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)
