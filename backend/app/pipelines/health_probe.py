"""健康探针：检测 Agent 和采集管道的频繁失败，自动产生系统自检告警"""

from datetime import datetime, timedelta

from sqlalchemy import select, func, and_

from app.constants import agent as constants_agent
from app.core.database import get_background_db_session, commit_or_rollback
from app.models.patrol_log import PatrolLog
from app.models.patrol_analysis import PatrolAnalysis
from app.models.alert import AlertEvent
from app.states.patrol import PatrolStatus
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)

# 分析失败摘要前缀
_ANALYSIS_FAILURE_PREFIXES = ("[分析失败]", "[分析超限]", "[执行超时]", "[分析异常]")


async def _count_patrol_failures(
    window_start: datetime,
) -> int:
    """统计采集管道在时间窗口内的 PARTIAL + FAILED 次数"""
    async with get_background_db_session() as db:
        count = await db.scalar(
            select(func.count(PatrolLog.id)).where(
                and_(
                    PatrolLog.executed_at >= window_start,
                    PatrolLog.status.in_([PatrolStatus.PARTIAL, PatrolStatus.FAILED]),
                )
            )
        )
    return count or 0


async def _count_analysis_failures(
    window_start: datetime,
) -> int:
    """统计 Analyst Agent 在时间窗口内的失败次数"""
    async with get_background_db_session() as db:
        results = (
            await db.scalars(
                select(PatrolAnalysis.summary).where(
                    PatrolAnalysis.analyzed_at >= window_start
                )
            )
        ).all()
    count = 0
    for summary in results:
        if summary and summary.startswith(_ANALYSIS_FAILURE_PREFIXES):
            count += 1
    return count


async def _has_active_self_alert(window_start: datetime) -> bool:
    """检查时间窗口内是否已有未关闭的系统自检告警（去重）"""
    async with get_background_db_session() as db:
        existing = await db.scalar(
            select(func.count(AlertEvent.id)).where(
                and_(
                    AlertEvent.source == 2,
                    AlertEvent.status < 3,
                    AlertEvent.detected_at >= window_start,
                )
            )
        )
    return (existing or 0) > 0


async def _create_health_alert(
    patrol_failures: int,
    analysis_failures: int,
    window_minutes: int,
) -> None:
    """创建系统自检告警"""
    total_failures = patrol_failures + analysis_failures
    title = "Agent 系统异常告警"

    if patrol_failures >= analysis_failures:
        alert_detail = (
            f"检测到 Agent 系统运行异常：过去 {window_minutes} 分钟内"
            f"采集管道失败 {patrol_failures} 次、"
            f"趋势分析失败 {analysis_failures} 次。"
        )
    else:
        alert_detail = (
            f"检测到 Agent 系统运行异常：过去 {window_minutes} 分钟内"
            f"趋势分析失败 {analysis_failures} 次、"
            f"采集管道失败 {patrol_failures} 次。"
        )

    async with get_background_db_session() as db:
        alert_entry = AlertEvent(
            reservoir_id=None,
            title=title,
            alert_level=2,
            indicators=[
                {
                    "name": "采集管道失败次数",
                    "value": patrol_failures,
                    "limit": constants_agent.HEALTH_ALERT_FAILURE_THRESHOLD,
                },
                {
                    "name": "趋势分析失败次数",
                    "value": analysis_failures,
                    "limit": constants_agent.HEALTH_ALERT_FAILURE_THRESHOLD,
                },
            ],
            source=2,
            status=0,
            detected_at=datetime.now(),
        )
        db.add(alert_entry)
        await commit_or_rollback(db)
        await db.refresh(alert_entry)
        logger.info(f"系统自检告警已创建: id={alert_entry.id}, detail={alert_detail}")


async def run_health_probe():
    """健康探针入口：APScheduler 定时调用

    逻辑：
    1. 统计过去 HEALTH_ALERT_WINDOW_MINUTES 分钟内
       PatrolLog 的 PARTIAL + FAILED 总数
    2. 统计 PatrolAnalysis 的失败记录总数
    3. 任一超过 HEALTH_ALERT_FAILURE_THRESHOLD → 检查去重
    4. 无重复告警 → 创建 AlertEvent(source=2)
    """
    now = datetime.now()
    window_start = now - timedelta(minutes=constants_agent.HEALTH_ALERT_WINDOW_MINUTES)

    try:
        patrol_failures = await _count_patrol_failures(window_start)
        analysis_failures = await _count_analysis_failures(window_start)

        total_failures = patrol_failures + analysis_failures
        logger.info(
            f"健康探针检测: 采集管道失败={patrol_failures}, "
            f"趋势分析失败={analysis_failures}, "
            f"阈值={constants_agent.HEALTH_ALERT_FAILURE_THRESHOLD}"
        )

        if total_failures < constants_agent.HEALTH_ALERT_FAILURE_THRESHOLD:
            logger.info("健康探针: 失败次数未达阈值，跳过")
            return

        if await _has_active_self_alert(window_start):
            logger.info("健康探针: 已有未关闭的系统自检告警，跳过")
            return

        await _create_health_alert(
            patrol_failures=patrol_failures,
            analysis_failures=analysis_failures,
            window_minutes=constants_agent.HEALTH_ALERT_WINDOW_MINUTES,
        )

    except Exception as e:
        logger.error(f"健康探针执行异常: {e}", exc_info=True)
