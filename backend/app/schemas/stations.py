from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========


class CreateMonitoringStationRequest(BaseModel):
    """创建监测站点请求模型"""

    reservoir_id: int = Field(..., description="水库ID")
    name: str = Field(..., description="站点名称")
    code: str = Field(..., description="站点编号")
    type: str | None = Field(None, description="站点类型")
    longitude: str | None = Field(None, description="经度")
    latitude: str | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")


class GetMonitoringStationListRequest(BaseModel):
    """获取监测站点列表请求模型"""

    reservoir_id: int | None = Field(None, description="水库ID")
    keyword: str | None = Field(None, description="站点名称")
    code: str | None = Field(None, description="站点编号")
    type: str | None = Field(None, description="站点类型")
    page: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class UpdateMonitoringStationRequest(BaseModel):
    """更新监测站点请求模型"""

    reservoir_id: int | None = Field(None, description="水库ID")
    name: str | None = Field(None, description="站点名称")
    code: str | None = Field(None, description="站点编号")
    type: str | None = Field(None, description="站点类型")
    longitude: str | None = Field(None, description="经度")
    latitude: str | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    status: int | None = Field(None, description="状态")


# ========== 响应类（Response）==========


class GetMonitoringStationListResponse(BaseModel):
    """获取监测站点列表响应模型"""

    id: int = Field(..., description="站点ID")
    name: str = Field(..., description="站点名称")
    code: str = Field(..., description="站点编号")
    reservoir_id: int = Field(..., description="水库ID")
    type: str | None = Field(None, description="站点类型")
    sampling_point: str | None = Field(None, description="采样点位描述")
    status: int = Field(..., description="状态")
    last_data_time: datetime | None = Field(None, description="最后数据时间")

    model_config = ConfigDict(from_attributes=True)


class GetMonitoringStationDetailResponse(BaseModel):
    """获取监测站点详情响应模型"""

    id: int = Field(..., description="站点ID")
    reservoir_id: int = Field(..., description="水库ID")
    name: str = Field(..., description="站点名称")
    code: str = Field(..., description="站点编号")
    type: str | None = Field(None, description="站点类型")
    longitude: str | None = Field(None, description="经度")
    latitude: str | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    status: int = Field(..., description="状态")

    model_config = ConfigDict(from_attributes=True)
