from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========


class GetReservoirListRequest(BaseModel):
    """获取水库列表请求参数"""

    keyword: str | None = Field(None, description="搜索关键词")
    watershed: str | None = Field(None, description="所属流域")
    water_grade: str | None = Field(None, description="水质等级")
    status: int | None = Field(None, description="状态 0停用 1启用")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=10, description="每页数量")


class CreateReservoirRequest(BaseModel):
    """创建水库请求参数"""

    name: str = Field(..., description="水库名称")
    code: str = Field(..., description="水库编号")
    location: str | None = Field(None, description="所在位置")
    longitude: str | None = Field(None, description="经度")
    latitude: str | None = Field(None, description="纬度")
    capacity: str | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级_Ⅱ类_Ⅲ类")
    watershed: str | None = Field(None, description="所属流域")
    sort_order: int = Field(0, description="排序")


# ========== 响应类（Response）==========


class GetReservoirListResponse(BaseModel):
    """获取水库列表响应参数"""

    name: str = Field(..., description="水库名称")
    code: str = Field(..., description="水库编号")
    capacity: str | None = Field(None, description="库容_万m3")
    water_grade: str | None = Field(None, description="水质等级_Ⅱ类_Ⅲ类")
    watershed: str | None = Field(None, description="所属流域")
    sort_order: int = Field(0, description="排序")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)
