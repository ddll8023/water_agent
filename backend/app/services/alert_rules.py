"""预警规则管理服务"""

import json
import math
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import alert_rule as models_alert_rule
from app.models import indicator as models_indicator
from app.models import alert as models_alert
from app.schemas import alert_rules as schemas_alert_rules
from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.utils.exception import ServiceException
from app.core.database import commit_or_rollback
from app.core.ws_manager import manager
from app.schemas import alerts as schemas_alerts
from app.utils.logger_config import setup_logger
from app.core.redis import get_redis, is_redis_available
from redis import Redis

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


def _evaluate_rule_trigger(
    rule: models_alert_rule.AlertRule,
    indicator_entity: models_indicator.Indicator,
    current_value: float,
) -> tuple[bool, Optional[float]]:
    """判断单条规则是否触发

    返回 (triggered, limit_value):
    - triggered=True 时 limit_value 为触发限值
    - triggered=False 时 limit_value 为 None

    规则：
    - compare_direction="gt"：current_value > standard_limit_{cls}_upper 时触发
    - compare_direction="lt"：current_value < standard_limit_{cls}_lower 时触发
    - 限值为空时不触发
    - 未知 compare_direction 时 warning 不触发
    """
    cls = rule.trigger_class.lower()

    if rule.compare_direction == "gt":
        limit = getattr(indicator_entity, f"standard_limit_{cls}_upper", None)
        if limit is None:
            return False, None
        triggered = current_value > float(limit)
        return (triggered, float(limit) if triggered else None)

    if rule.compare_direction == "lt":
        limit = getattr(indicator_entity, f"standard_limit_{cls}_lower", None)
        if limit is None:
            return False, None
        triggered = current_value < float(limit)
        return (triggered, float(limit) if triggered else None)

    logger.warning(
        f"未知的 compare_direction: {rule.compare_direction}, rule_id={rule.id}"
    )
    return False, None


async def broadcast_alert(alert_entity: models_alert.AlertEvent, event_type: str = "new_alert"):
    """广播预警事件到 WebSocket"""
    try:
        alert_data = schemas_alerts.GetAlertDetailResponse.model_validate(alert_entity)
        await manager.broadcast(
            {
                "type": event_type,
                "data": alert_data.model_dump(mode="json"),
            }
        )
    except Exception as e:
        logger.error(
            f"预警 WebSocket 广播失败: alert_id={alert_entity.id}, "
            f"event_type={event_type}, error={e}"
        )


async def cache_alert_to_redis(alert_entity: models_alert.AlertEvent):
    """缓存最近 5 条规则预警到 Redis（只缓存 source=0）"""
    try:
        if not await is_redis_available():
            return
        if alert_entity.source != 0:
            return
        key = "alert:recent"
        redis_client: Redis = await get_redis()

        alert_dict = {
            "id": alert_entity.id,
            "reservoir_id": alert_entity.reservoir_id,
            "title": alert_entity.title,
            "alert_level": alert_entity.alert_level,
            "indicators": alert_entity.indicators,
            "source": alert_entity.source,
            "status": alert_entity.status,
            "detected_at": alert_entity.detected_at.isoformat() if alert_entity.detected_at else None,
        }
        alert_json = json.dumps(alert_dict, ensure_ascii=False)

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
    except Exception as e:
        logger.error(f"预警 Redis 缓存失败: alert_id={alert_entity.id}, error={e}")
