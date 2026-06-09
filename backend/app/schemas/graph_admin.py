"""河流与污染源管理 Schema"""

from pydantic import BaseModel, ConfigDict, Field


# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========


class CreateRiverRequest(BaseModel):
    """创建河流请求参数"""

    name: str = Field(..., description="河流名称")
    length: float | None = Field(None, description="长度(km)")
    watershed: str | None = Field(None, description="所属流域")
    flows_into_reservoir_code: str | None = Field(None, description="注入水库编号")


class UpdateRiverRequest(BaseModel):
    """更新河流请求参数"""

    length: float | None = Field(None, description="长度(km)")
    watershed: str | None = Field(None, description="所属流域")
    flows_into_reservoir_code: str | None = Field(None, description="注入水库编号")


class CreatePollutionSourceRequest(BaseModel):
    """创建污染源请求参数"""

    name: str = Field(..., description="污染源名称")
    type: str = Field(..., description="类型：养殖场/工业企业/农业面源/其他")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    risk_level: str = Field(..., description="风险等级：高/中/低")
    violation_count: int = Field(default=0, description="违规次数")
    discharges_into_river_name: str | None = Field(None, description="排入河流名称")
    distance_km: float | None = Field(None, description="距水库距离(km)")


class UpdatePollutionSourceRequest(BaseModel):
    """更新污染源请求参数"""

    name: str | None = Field(None, description="污染源名称")
    type: str | None = Field(None, description="类型")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    risk_level: str | None = Field(None, description="风险等级")
    violation_count: int | None = Field(None, description="违规次数")
    discharges_into_river_name: str | None = Field(None, description="排入河流名称")
    distance_km: float | None = Field(None, description="距水库距离(km)")


# ========== 响应类（Response）==========


class GetRiverListResponse(BaseModel):
    """河流列表响应"""

    name: str = Field(..., description="河流名称")
    length: float | None = Field(None, description="长度(km)")
    watershed: str | None = Field(None, description="所属流域")
    flows_into_reservoir_code: str | None = Field(None, description="注入水库编号")

    model_config = ConfigDict(from_attributes=True)


class GetRiverDetailResponse(BaseModel):
    """河流详情响应"""

    name: str = Field(..., description="河流名称")
    length: float | None = Field(None, description="长度(km)")
    watershed: str | None = Field(None, description="所属流域")
    flows_into_reservoir_code: str | None = Field(None, description="注入水库编号")

    model_config = ConfigDict(from_attributes=True)


class GetPollutionSourceListResponse(BaseModel):
    """污染源列表响应"""

    name: str = Field(..., description="污染源名称")
    type: str = Field(..., description="类型")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    risk_level: str = Field(..., description="风险等级")
    violation_count: int = Field(..., description="违规次数")
    discharges_into_river_name: str | None = Field(None, description="排入河流名称")
    distance_km: float | None = Field(None, description="距水库距离(km)")

    model_config = ConfigDict(from_attributes=True)


class GetPollutionSourceDetailResponse(BaseModel):
    """污染源详情响应"""

    name: str = Field(..., description="污染源名称")
    type: str = Field(..., description="类型")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    risk_level: str = Field(..., description="风险等级")
    violation_count: int = Field(..., description="违规次数")
    discharges_into_river_name: str | None = Field(None, description="排入河流名称")
    distance_km: float | None = Field(None, description="距水库距离(km)")

    model_config = ConfigDict(from_attributes=True)


class CreateNeo4jReservoirRequest(BaseModel):
    """创建水库（Neo4j直写）请求参数"""

    code: str = Field(..., description="水库编号")
    name: str = Field(..., description="水库名称")
    location: str | None = Field(None, description="所在位置")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    capacity: float | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级")
    watershed: str | None = Field(None, description="所属流域")


class UpdateNeo4jReservoirRequest(BaseModel):
    """更新水库（Neo4j直写）请求参数"""

    name: str | None = Field(None, description="水库名称")
    location: str | None = Field(None, description="所在位置")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    capacity: float | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级")
    watershed: str | None = Field(None, description="所属流域")


class GetNeo4jReservoirListResponse(BaseModel):
    """水库列表响应（Neo4j直写）"""

    code: str = Field(..., description="水库编号")
    name: str = Field(..., description="水库名称")
    location: str | None = Field(None, description="所在位置")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    capacity: float | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级")
    watershed: str | None = Field(None, description="所属流域")

    model_config = ConfigDict(from_attributes=True)


class GetNeo4jReservoirDetailResponse(BaseModel):
    """水库详情响应（Neo4j直写）"""

    code: str = Field(..., description="水库编号")
    name: str = Field(..., description="水库名称")
    location: str | None = Field(None, description="所在位置")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    capacity: float | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级")
    watershed: str | None = Field(None, description="所属流域")

    model_config = ConfigDict(from_attributes=True)


class CreateNeo4jStationRequest(BaseModel):
    """创建监测站点（Neo4j直写）请求参数"""

    code: str = Field(..., description="站点编号")
    name: str = Field(..., description="站点名称")
    type: str = Field(..., description="站点类型：auto/manual/sensing")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    reservoir_code: str | None = Field(None, description="所属水库编号（用于BELONGS_TO关系）")


class UpdateNeo4jStationRequest(BaseModel):
    """更新监测站点（Neo4j直写）请求参数"""

    name: str | None = Field(None, description="站点名称")
    type: str | None = Field(None, description="站点类型")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    reservoir_code: str | None = Field(None, description="所属水库编号")


class GetNeo4jStationListResponse(BaseModel):
    """监测站点列表响应（Neo4j直写）"""

    code: str = Field(..., description="站点编号")
    name: str = Field(..., description="站点名称")
    type: str | None = Field(None, description="站点类型")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    reservoir_code: str | None = Field(None, description="所属水库编号")

    model_config = ConfigDict(from_attributes=True)


class GetNeo4jStationDetailResponse(BaseModel):
    """监测站点详情响应（Neo4j直写）"""

    code: str = Field(..., description="站点编号")
    name: str = Field(..., description="站点名称")
    type: str | None = Field(None, description="站点类型")
    longitude: float | None = Field(None, description="经度")
    latitude: float | None = Field(None, description="纬度")
    sampling_point: str | None = Field(None, description="采样点位描述")
    reservoir_code: str | None = Field(None, description="所属水库编号")

    model_config = ConfigDict(from_attributes=True)


class CreateNeo4jIndicatorRequest(BaseModel):
    """创建监测指标（Neo4j直写）请求参数"""

    code: str = Field(..., description="指标编码")
    name: str = Field(..., description="指标名称")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类：物理/化学/生物")


class UpdateNeo4jIndicatorRequest(BaseModel):
    """更新监测指标（Neo4j直写）请求参数"""

    name: str | None = Field(None, description="指标名称")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")


class GetNeo4jIndicatorListResponse(BaseModel):
    """监测指标列表响应（Neo4j直写）"""

    code: str = Field(..., description="指标编码")
    name: str = Field(..., description="指标名称")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")

    model_config = ConfigDict(from_attributes=True)


class GetNeo4jIndicatorDetailResponse(BaseModel):
    """监测指标详情响应（Neo4j直写）"""

    code: str = Field(..., description="指标编码")
    name: str = Field(..., description="指标名称")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")

    model_config = ConfigDict(from_attributes=True)
