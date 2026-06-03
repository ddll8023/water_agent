"""预警规则管理服务"""

import math
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import alert_rule as models_alert_rule
from app.models import indicator as models_indicator
from app.models import alert as models_alert
from app.models import reservoir as models_reservoir
from app.schemas import alert_rules as schemas_alert_rules
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.core.database import commit_or_rollback
from app.core.ws_manager import manager
from app.schemas import alerts as schemas_alerts


async def create_alert_rule(
    db: AsyncSession,
    create_alert_rule_request: schemas_alert_rules.CreateAlertRuleRequest,
):
    """创建预警规则"""
    indicator = await db.get(
        models_indicator.Indicator, create_alert_rule_request.indicator_id
    )
    if not indicator:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "关联指标不存在")

    rule = models_alert_rule.AlertRule(**create_alert_rule_request.model_dump())
    db.add(rule)
    await commit_or_rollback(db)
    return True


async def get_alert_rule_list(
    db: AsyncSession,
    get_alert_rule_list_request: schemas_alert_rules.GetAlertRuleListRequest,
):
    """获取预警规则列表"""
    base_stmt = select(models_alert_rule.AlertRule)

    if get_alert_rule_list_request.indicator_id is not None:
        base_stmt = base_stmt.where(
            models_alert_rule.AlertRule.indicator_id
            == get_alert_rule_list_request.indicator_id
        )
    if get_alert_rule_list_request.reservoir_id is not None:
        base_stmt = base_stmt.where(
            models_alert_rule.AlertRule.reservoir_id
            == get_alert_rule_list_request.reservoir_id
        )
    if get_alert_rule_list_request.is_active is not None:
        base_stmt = base_stmt.where(
            models_alert_rule.AlertRule.is_active
            == get_alert_rule_list_request.is_active
        )

    total = await db.scalar(select(func.count()).select_from(base_stmt.subquery()))

    items = (
        await db.scalars(
            base_stmt.order_by(models_alert_rule.AlertRule.id)
            .offset(
                (get_alert_rule_list_request.page - 1)
                * get_alert_rule_list_request.page_size
            )
            .limit(get_alert_rule_list_request.page_size)
        )
    ).all()

    return PaginatedResponse(
        lists=[
            schemas_alert_rules.GetAlertRuleListResponse.model_validate(item)
            for item in items
        ],
        pagination=PaginationInfo(
            page=get_alert_rule_list_request.page,
            page_size=get_alert_rule_list_request.page_size,
            total=total or 0,
            total_pages=math.ceil((total or 0) / get_alert_rule_list_request.page_size),
        ),
    )


async def get_alert_rule_detail(
    db: AsyncSession,
    rule_id: int,
):
    """获取预警规则详情"""
    rule = await db.get(models_alert_rule.AlertRule, rule_id)
    if not rule:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "规则不存在")
    return schemas_alert_rules.GetAlertRuleDetailResponse.model_validate(rule)


async def update_alert_rule(
    db: AsyncSession,
    rule_id: int,
    request: schemas_alert_rules.UpdateAlertRuleRequest,
):
    """更新预警规则"""
    rule = await db.get(models_alert_rule.AlertRule, rule_id)
    if not rule:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "规则不存在")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await commit_or_rollback(db)
    return True


async def delete_alert_rule(
    db: AsyncSession,
    rule_id: int,
):
    """删除预警规则"""
    rule = await db.get(models_alert_rule.AlertRule, rule_id)
    if not rule:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "规则不存在")
    await db.delete(rule)
    await commit_or_rollback(db)
    return True


async def evaluate_alert_rules(
    db: AsyncSession,
    indicator_id: int,
    reservoir_id: int,
    indicator_entity: models_indicator.Indicator,
    current_value: float,
    record_time: datetime,
):
    """对单条监测记录执行预警规则判定"""
    rules = await _get_matched_rules(db, indicator_id, reservoir_id)
    if not rules:
        return False

    has_unresolved = await _has_unresolved_alert(db, reservoir_id)
    if has_unresolved:
        return False

    triggered_items = []
    for rule in rules:
        limit = _resolve_limit(
            indicator_entity, rule.trigger_class, rule.compare_direction
        )
        if limit is None:
            continue

        if rule.compare_direction == "gt" and current_value > limit:
            triggered_items.append(
                {
                    "rule": rule,
                    "limit": float(limit),
                }
            )
        elif rule.compare_direction == "lt" and current_value < limit:
            triggered_items.append(
                {
                    "rule": rule,
                    "limit": float(limit),
                }
            )

    if not triggered_items:
        return False

    reservoir = await db.get(models_reservoir.Reservoir, reservoir_id)
    reservoir_name = reservoir.name if reservoir else f"水库{reservoir_id}"

    max_level_item = max(triggered_items, key=lambda x: x["rule"].alert_level)
    rule = max_level_item["rule"]
    limit = max_level_item["limit"]

    title = f"{reservoir_name}指标告警（{indicator_entity.name}={current_value}, 限值={limit}{indicator_entity.unit or ''}）"
    alert_indicators = [
        {
            "name": indicator_entity.name,
            "value": current_value,
            "limit": limit,
            "unit": indicator_entity.unit or "",
        }
    ]

    alert = models_alert.AlertEvent(
        reservoir_id=reservoir_id,
        title=title,
        alert_level=rule.alert_level,
        indicators=alert_indicators,
        status=0,
        detected_at=record_time,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)

    try:
        alert_data = schemas_alerts.GetAlertDetailResponse.model_validate(alert)
        await manager.broadcast(
            {
                "type": "new_alert",
                "data": alert_data.model_dump(mode="json"),
            }
        )
    except Exception:
        pass
    return True


"""辅助函数"""


def _resolve_limit(
    indicator: models_indicator.Indicator,
    trigger_class: str,
    direction: str,
) -> float | None:
    """从指标实体中按等级+方向读取限值"""
    cls = trigger_class.lower()
    if direction == "gt":
        return getattr(indicator, f"standard_limit_{cls}_upper", None)
    return getattr(indicator, f"standard_limit_{cls}_lower", None)


async def _get_matched_rules(db: AsyncSession, indicator_id: int, reservoir_id: int):
    """查询匹配的预警规则（水库级优先，回退全局规则）"""
    stmt = select(models_alert_rule.AlertRule).where(
        and_(
            models_alert_rule.AlertRule.indicator_id == indicator_id,
            models_alert_rule.AlertRule.is_active == 1,
            or_(
                models_alert_rule.AlertRule.reservoir_id == reservoir_id,
                models_alert_rule.AlertRule.reservoir_id.is_(None),
            ),
        )
    )
    rules = (await db.scalars(stmt)).all()

    reservoir_rules = [r for r in rules if r.reservoir_id == reservoir_id]
    matched_ids = {r.indicator_id for r in reservoir_rules}
    for g in rules:
        if g.reservoir_id is None and g.indicator_id not in matched_ids:
            reservoir_rules.append(g)

    return reservoir_rules


async def _has_unresolved_alert(db: AsyncSession, reservoir_id: int) -> bool:
    """检查该水库是否存在未关闭预警"""
    stmt = select(models_alert.AlertEvent).where(
        and_(
            models_alert.AlertEvent.reservoir_id == reservoir_id,
            models_alert.AlertEvent.status < 3,
        )
    )
    entity = await db.scalar(stmt)
    return entity is not None
