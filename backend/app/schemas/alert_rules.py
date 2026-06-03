from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ========== 辅助类（Support）==========


# ========== 请求类（Request）==========

class CreateAlertRuleRequest(BaseModel):
    """创建预警规则请求"""

    rule_name: str = Field(..., description="规则名称")
    indicator_id: int = Field(..., description="关联指标ID")
    reservoir_id: int | None = Field(None, description="水库ID，null=全局规则")
    compare_direction: str = Field(
        ..., description="比较方向：gt=超上限告警 lt=低下限告警"
    )
    trigger_class: str = Field(
        ..., description="触发限值等级：I/II/III/IV/V"
    )
    alert_level: int = Field(
        ..., description="预警等级：1=info 2=warning 3=critical"
    )
    is_active: int | None = Field(1, description="是否启用：0禁用 1启用")
    remark: str | None = Field(None, description="备注说明")


class UpdateAlertRuleRequest(BaseModel):
    """更新预警规则请求"""

    rule_name: str | None = Field(None, description="规则名称")
    indicator_id: int | None = Field(None, description="关联指标ID")
    reservoir_id: int | None = Field(None, description="水库ID，null=全局规则")
    compare_direction: str | None = Field(
        None, description="比较方向：gt=超上限告警 lt=低下限告警"
    )
    trigger_class: str | None = Field(
        None, description="触发限值等级：I/II/III/IV/V"
    )
    alert_level: int | None = Field(
        None, description="预警等级：1=info 2=warning 3=critical"
    )
    is_active: int | None = Field(None, description="是否启用：0禁用 1启用")
    remark: str | None = Field(None, description="备注说明")


class GetAlertRuleListRequest(BaseModel):
    """获取预警规则列表请求"""

    indicator_id: int | None = Field(None, description="指标ID筛选")
    reservoir_id: int | None = Field(None, description="水库ID筛选")
    is_active: int | None = Field(None, description="启用状态筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")


# ========== 响应类（Response）==========

class GetAlertRuleListResponse(BaseModel):
    """预警规则列表响应"""

    id: int = Field(description="规则ID")
    rule_name: str = Field(description="规则名称")
    indicator_id: int = Field(description="关联指标ID")
    reservoir_id: int | None = Field(None, description="水库ID")
    compare_direction: str = Field(description="比较方向")
    trigger_class: str = Field(description="触发限值等级")
    alert_level: int = Field(description="预警等级")
    is_active: int = Field(description="是否启用")

    model_config = ConfigDict(from_attributes=True)


class GetAlertRuleDetailResponse(BaseModel):
    """预警规则详情响应"""

    id: int = Field(description="规则ID")
    rule_name: str = Field(description="规则名称")
    indicator_id: int = Field(description="关联指标ID")
    reservoir_id: int | None = Field(None, description="水库ID")
    compare_direction: str = Field(description="比较方向")
    trigger_class: str = Field(description="触发限值等级")
    alert_level: int = Field(description="预警等级")
    is_active: int = Field(description="是否启用")
    remark: str | None = Field(None, description="备注说明")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    model_config = ConfigDict(from_attributes=True)
