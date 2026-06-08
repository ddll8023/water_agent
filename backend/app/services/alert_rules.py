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
from app.utils.logger_config import setup_logger
from app.core.redis import get_redis, is_redis_available
from redis import Redis
import json

logger = setup_logger(__name__)


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
        logger.info(f"没有匹配的预警规则，指标ID={indicator_id}，水库ID={reservoir_id}")
        return False

    triggered_items = []
    for rule in rules:
        cls = rule.trigger_class.lower()
        if rule.compare_direction == "gt":
            limit = getattr(indicator_entity, f"standard_limit_{cls}_upper", None)
        else:
            limit = getattr(indicator_entity, f"standard_limit_{cls}_lower", None)

        if limit is None:
            continue

        if current_value > limit:
            triggered_items.append(
                {
                    "rule": rule,
                    "limit": float(limit),
                }
            )
        elif current_value < limit:
            triggered_items.append(
                {
                    "rule": rule,
                    "limit": float(limit),
                }
            )

    if not triggered_items:
        return False

    reservoir = await db.get(models_reservoir.Reservoir, reservoir_id)

    max_level_item = max(triggered_items, key=lambda x: x["rule"].alert_level)
    rule = max_level_item["rule"]
    limit = max_level_item["limit"]

    alert_indicator_entry = {
        "indicator_id": indicator_id,
        "name": indicator_entity.name,
        "value": current_value,
        "limit": limit,
        "unit": indicator_entity.unit or "",
    }

    # 查找该水库是否有未关闭预警 → 用于合并
    existing_alert = await db.scalar(
        select(models_alert.AlertEvent).where(
            and_(
                models_alert.AlertEvent.reservoir_id == reservoir_id,
                models_alert.AlertEvent.status < 3,
            )
        ).order_by(models_alert.AlertEvent.detected_at.asc()).limit(1)
    )

    if existing_alert:
        existing_inds = existing_alert.indicators or []
        existing_indicator_ids = {ind.get("indicator_id") for ind in existing_inds}

        if indicator_id in existing_indicator_ids:
            logger.info(f"该指标已在未关闭预警中，跳过: indicator_id={indicator_id}")
            return False

        # 不同指标 → 合并到现有预警
        existing_inds.append(alert_indicator_entry)
        existing_alert.indicators = existing_inds
        existing_alert.alert_level = max(existing_alert.alert_level, rule.alert_level)
        existing_alert.title = f"{reservoir.name}多指标复合告警（共{len(existing_inds)}项指标异常）"

        await db.flush()
        await db.refresh(existing_alert)
        await _cache_to_redis(existing_alert)
        await _broadcast_alert(existing_alert, "alert_updated")
        return True

    # 无未关闭预警 → 创建新预警
    title = f"{reservoir.name}指标告警（{indicator_entity.name}={current_value}, 限值={limit}{indicator_entity.unit or ''}）"
    alert_indicators = [alert_indicator_entry]

    alert_entity = models_alert.AlertEvent(
        reservoir_id=reservoir_id,
        title=title,
        alert_level=rule.alert_level,
        indicators=alert_indicators,
        status=0,
        detected_at=record_time,
    )
    db.add(alert_entity)
    await db.flush()
    await db.refresh(alert_entity)
    await _cache_to_redis(alert_entity)
    await _broadcast_alert(alert_entity, "new_alert")
    return True


"""辅助函数"""


async def _get_matched_rules(db: AsyncSession, indicator_id: int, reservoir_id: int):
    """查询匹配的预警规则"""
    rules = (
        await db.scalars(
            select(models_alert_rule.AlertRule).where(
                and_(
                    models_alert_rule.AlertRule.indicator_id == indicator_id,
                    models_alert_rule.AlertRule.is_active == 1,
                    or_(
                        models_alert_rule.AlertRule.reservoir_id == reservoir_id,
                        models_alert_rule.AlertRule.reservoir_id.is_(None),
                    ),
                )
            )
        )
    ).all()

    reservoir_rules = [r for r in rules if r.reservoir_id == reservoir_id]
    matched_ids = {r.indicator_id for r in reservoir_rules}
    for g in rules:
        if g.reservoir_id is None and g.indicator_id not in matched_ids:
            reservoir_rules.append(g)

    return reservoir_rules


async def _broadcast_alert(alert_entity: models_alert.AlertEvent, event_type: str = "new_alert"):
    """广播预警事件到 WebSocket"""
    try:
        alert_data = schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)
        await manager.broadcast(
            {
                "type": event_type,
                "data": alert_data.model_dump(mode="json"),
            }
        )
    except Exception:
        pass


async def _cache_to_redis(alert_entity: models_alert.AlertEvent):
    """缓存最近 5 条预警到 Redis（lpush + 去旧补新）"""
    if not await is_redis_available():
        return
    key = "alert:recent"
    redis_client: Redis = await get_redis()

    alert_dict = {
        "id": alert_entity.id,
        "reservoir_id": alert_entity.reservoir_id,
        "title": alert_entity.title,
        "alert_level": alert_entity.alert_level,
        "indicators": alert_entity.indicators,
        "status": alert_entity.status,
        "detected_at": alert_entity.detected_at.isoformat() if alert_entity.detected_at else None,
    }
    alert_json = json.dumps(alert_dict, ensure_ascii=False)

    # 删除同 ID 的旧条目（合并场景需要更新旧条目）
    existing = await redis_client.lrange(key, 0, -1)
    for item in existing:
        try:
            raw = item if isinstance(item, str) else item.decode()
            if json.loads(raw).get("id") == alert_entity.id:
                await redis_client.lrem(key, 0, item)
        except Exception:
            continue

    await redis_client.lpush(key, alert_json)
    await redis_client.ltrim(key, 0, 4)
