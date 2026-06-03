from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========


class CreateIndicatorRequest(BaseModel):
    """创建指标请求"""

    name: str = Field(..., description="指标名称")
    code: str = Field(..., description="指标编码")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")
    standard_limit_i_lower: float | None = Field(None, description="Ⅰ类下限值")
    standard_limit_i_upper: float | None = Field(None, description="Ⅰ类上限值")
    standard_limit_ii_lower: float | None = Field(None, description="Ⅱ类下限值")
    standard_limit_ii_upper: float | None = Field(None, description="Ⅱ类上限值")
    standard_limit_iii_lower: float | None = Field(None, description="Ⅲ类下限值")
    standard_limit_iii_upper: float | None = Field(None, description="Ⅲ类上限值")
    standard_limit_iv_lower: float | None = Field(None, description="Ⅳ类下限值")
    standard_limit_iv_upper: float | None = Field(None, description="Ⅳ类上限值")
    standard_limit_v_lower: float | None = Field(None, description="Ⅴ类下限值")
    standard_limit_v_upper: float | None = Field(None, description="Ⅴ类上限值")
    is_core: int | None = Field(None, description="是否核心指标")


class GetIndicatorListRequest(BaseModel):
    """获取指标列表请求"""

    name: str | None = Field(None, description="指标名称")
    code: str | None = Field(None, description="指标编码")
    category: str | None = Field(None, description="分类")
    is_core: int | None = Field(None, description="是否核心指标")
    page: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class UpdateIndicatorRequest(BaseModel):
    """更新指标请求"""

    name: str | None = Field(None, description="指标名称")
    code: str | None = Field(None, description="指标编码")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")
    standard_limit_i_lower: float | None = Field(None, description="Ⅰ类下限值")
    standard_limit_i_upper: float | None = Field(None, description="Ⅰ类上限值")
    standard_limit_ii_lower: float | None = Field(None, description="Ⅱ类下限值")
    standard_limit_ii_upper: float | None = Field(None, description="Ⅱ类上限值")
    standard_limit_iii_lower: float | None = Field(None, description="Ⅲ类下限值")
    standard_limit_iii_upper: float | None = Field(None, description="Ⅲ类上限值")
    standard_limit_iv_lower: float | None = Field(None, description="Ⅳ类下限值")
    standard_limit_iv_upper: float | None = Field(None, description="Ⅳ类上限值")
    standard_limit_v_lower: float | None = Field(None, description="Ⅴ类下限值")
    standard_limit_v_upper: float | None = Field(None, description="Ⅴ类上限值")
    is_core: int | None = Field(None, description="是否核心指标")


# ========== 响应类（Response）==========


class GetIndicatorListResponse(BaseModel):
    """获取指标列表响应"""

    id: int = Field(..., description="指标ID")
    name: str = Field(..., description="指标名称")
    code: str = Field(..., description="指标编码")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")
    standard_limit_i_lower: float | None = Field(None, description="Ⅰ类下限值")
    standard_limit_i_upper: float | None = Field(None, description="Ⅰ类上限值")
    standard_limit_ii_lower: float | None = Field(None, description="Ⅱ类下限值")
    standard_limit_ii_upper: float | None = Field(None, description="Ⅱ类上限值")
    standard_limit_iii_lower: float | None = Field(None, description="Ⅲ类下限值")
    standard_limit_iii_upper: float | None = Field(None, description="Ⅲ类上限值")
    standard_limit_iv_lower: float | None = Field(None, description="Ⅳ类下限值")
    standard_limit_iv_upper: float | None = Field(None, description="Ⅳ类上限值")
    standard_limit_v_lower: float | None = Field(None, description="Ⅴ类下限值")
    standard_limit_v_upper: float | None = Field(None, description="Ⅴ类上限值")
    is_core: int | None = Field(None, description="是否核心指标")

    model_config = ConfigDict(from_attributes=True)


class GetIndicatorDetailResponse(BaseModel):
    """获取指标详情响应"""

    id: int = Field(..., description="指标ID")
    name: str = Field(..., description="指标名称")
    code: str = Field(..., description="指标编码")
    unit: str | None = Field(None, description="单位")
    category: str | None = Field(None, description="分类")
    standard_limit_i_lower: float | None = Field(None, description="Ⅰ类下限值")
    standard_limit_i_upper: float | None = Field(None, description="Ⅰ类上限值")
    standard_limit_ii_lower: float | None = Field(None, description="Ⅱ类下限值")
    standard_limit_ii_upper: float | None = Field(None, description="Ⅱ类上限值")
    standard_limit_iii_lower: float | None = Field(None, description="Ⅲ类下限值")
    standard_limit_iii_upper: float | None = Field(None, description="Ⅲ类上限值")
    standard_limit_iv_lower: float | None = Field(None, description="Ⅳ类下限值")
    standard_limit_iv_upper: float | None = Field(None, description="Ⅳ类上限值")
    standard_limit_v_lower: float | None = Field(None, description="Ⅴ类下限值")
    standard_limit_v_upper: float | None = Field(None, description="Ⅴ类上限值")
    is_core: int | None = Field(None, description="是否核心指标")

    model_config = ConfigDict(from_attributes=True)
