"""Report Generator Pipeline：定时聚合数据→LLM 生成报告→写入 report 表"""

import json
from datetime import datetime, timedelta

from sqlalchemy import select, func
from app.states.report import ReportStatus, ReportType
from app.core.database import get_background_db_session, commit_or_rollback
from app.models.report import Report as models_report
from app.models.patrol_log import PatrolLog
from app.models.patrol_analysis import PatrolAnalysis
from app.models.alert import AlertEvent
from app.models.monitoring import MonitoringRecord
from app.models.indicator import Indicator
from app.models.reservoir import Reservoir
from app.utils.logger_config import setup_logger
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt
from app.schemas import report as schemas_report
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

logger = setup_logger(__name__)


async def collect_report_data(report_type, alert_id=None):
    """按报告类型聚合多源监测数据"""
    now = datetime.now()
    if report_type == ReportType.DAILY:
        period_end = now
        period_start = now - timedelta(hours=24)
    elif report_type == ReportType.QUARTERLY:
        period_end = now
        period_start = now - timedelta(days=90)
    elif report_type == ReportType.EVENT:
        period_end = now
        period_start = now - timedelta(days=7)

    try:
        async with get_background_db_session() as db:
            patrol_summary = None
            alert_stats = None
            indicator_stats = None
            analysis_summary = None
            monthly_trend = None
            period_comparison = None
            trace_info = ""
            process_detail = ""

            if report_type in (ReportType.DAILY, ReportType.QUARTERLY):
                # 1. 巡检日志统计
                log_counts = (
                    await db.execute(
                        select(
                            PatrolLog.status,
                            func.count(PatrolLog.id),
                            func.coalesce(func.sum(PatrolLog.record_count), 0),
                        )
                        .where(
                            PatrolLog.executed_at >= period_start,
                            PatrolLog.executed_at <= period_end,
                        )
                        .group_by(PatrolLog.status)
                    )
                ).all()

                success_count = 0
                partial_count = 0
                failed_count = 0
                total_records = 0
                for status, cnt, recs in log_counts:
                    if status == 0:
                        success_count = cnt
                    elif status == 1:
                        partial_count = cnt
                    elif status == 2:
                        failed_count = cnt
                    total_records += recs

                patrol_summary = {
                    "success_count": success_count,
                    "partial_count": partial_count,
                    "failed_count": failed_count,
                    "total_executions": success_count + partial_count + failed_count,
                    "total_records": total_records,
                }

                # 2. 预警事件统计
                alert_counts = (
                    await db.execute(
                        select(
                            AlertEvent.alert_level,
                            func.count(AlertEvent.id),
                        )
                        .where(
                            AlertEvent.detected_at >= period_start,
                            AlertEvent.detected_at <= period_end,
                        )
                        .group_by(AlertEvent.alert_level)
                    )
                ).all()

                by_level = {1: 0, 2: 0, 3: 0}
                for level, cnt in alert_counts:
                    by_level[level] = cnt

                pending_count = (
                    await db.scalar(
                        select(func.count(AlertEvent.id)).where(
                            AlertEvent.detected_at >= period_start,
                            AlertEvent.detected_at <= period_end,
                            AlertEvent.status < 3,
                        )
                    )
                ) or 0

                rule_alert_count = (
                    await db.scalar(
                        select(func.count(AlertEvent.id)).where(
                            AlertEvent.detected_at >= period_start,
                            AlertEvent.detected_at <= period_end,
                            AlertEvent.source == 0,
                        )
                    )
                ) or 0

                ai_alert_count = (
                    await db.scalar(
                        select(func.count(AlertEvent.id)).where(
                            AlertEvent.detected_at >= period_start,
                            AlertEvent.detected_at <= period_end,
                            AlertEvent.source == 1,
                        )
                    )
                ) or 0

                alert_stats = {
                    "total": sum(by_level.values()),
                    "by_level": by_level,
                    "pending": pending_count,
                    "rule_alerts": rule_alert_count,
                    "ai_alerts": ai_alert_count,
                }

                # 3. 核心指标各水库均值
                indicators = (
                    await db.scalars(select(Indicator).where(Indicator.is_core == 1))
                ).all()

                if indicators:
                    ind_ids = [ind.id for ind in indicators]
                    ind_map = {
                        ind.id: {"name": ind.name, "unit": ind.unit}
                        for ind in indicators
                    }

                    rows = (
                        await db.execute(
                            select(
                                MonitoringRecord.reservoir_id,
                                MonitoringRecord.indicator_id,
                                func.avg(MonitoringRecord.value),
                            )
                            .where(
                                MonitoringRecord.record_time >= period_start,
                                MonitoringRecord.record_time <= period_end,
                                MonitoringRecord.indicator_id.in_(ind_ids),
                            )
                            .group_by(
                                MonitoringRecord.reservoir_id,
                                MonitoringRecord.indicator_id,
                            )
                        )
                    ).all()

                    reservoir_ids = {row[0] for row in rows}
                    reservoirs = (
                        await db.scalars(
                            select(Reservoir).where(Reservoir.id.in_(reservoir_ids))
                        )
                    ).all()
                    reservoir_map = {res.id: res.name for res in reservoirs}

                    indicator_stats = [
                        {
                            "reservoir_name": reservoir_map.get(row[0], str(row[0])),
                            "indicator_name": ind_map.get(row[1], {}).get(
                                "name", str(row[1])
                            ),
                            "avg_value": round(float(row[2]), 4),
                            "unit": ind_map.get(row[1], {}).get("unit", ""),
                        }
                        for row in rows
                    ]

                # 4. 最新分析摘要
                latest_analysis = (
                    await db.scalars(
                        select(PatrolAnalysis)
                        .order_by(PatrolAnalysis.analyzed_at.desc())
                        .limit(1)
                    )
                ).first()
                if latest_analysis:
                    analysis_summary = [
                        {
                            "analyzed_at": latest_analysis.analyzed_at.isoformat(),
                            "summary": latest_analysis.summary,
                        }
                    ]

                # 5. QUARTERLY 月度趋势 + 同期对比
                if report_type == ReportType.QUARTERLY:
                    monthly_trend = []
                    for i in [2, 1, 0]:
                        ref = period_start.replace(day=1) - timedelta(days=30 * i)
                        ms = ref.replace(day=1)
                        me = (ms + timedelta(days=32)).replace(day=1)
                        cnt = (
                            await db.scalar(
                                select(func.count(AlertEvent.id)).where(
                                    AlertEvent.detected_at >= ms,
                                    AlertEvent.detected_at < me,
                                )
                            )
                            or 0
                        )
                        monthly_trend.append(
                            {"month": ms.strftime("%Y-%m"), "count": cnt}
                        )

                    prev_start = period_start - timedelta(days=90)
                    prev_total = (
                        await db.scalar(
                            select(func.count(AlertEvent.id)).where(
                                AlertEvent.detected_at >= prev_start,
                                AlertEvent.detected_at < period_start,
                            )
                        )
                        or 0
                    )
                    current_total = sum(m["count"] for m in monthly_trend)
                    period_comparison = {
                        "previous_total": prev_total,
                        "current_total": current_total,
                        "change_percent": round(
                            (current_total - prev_total) / max(prev_total, 1) * 100, 1
                        ),
                    }

            elif report_type == ReportType.EVENT and alert_id:
                alert = await db.get(AlertEvent, alert_id)
                if alert:
                    alert_stats = {
                        "title": alert.title,
                        "alert_level": alert.alert_level,
                        "detected_at": (
                            alert.detected_at.isoformat() if alert.detected_at else None
                        ),
                        "status": alert.status,
                        "indicators": alert.indicators,
                        "suggestion": alert.suggestion,
                    }

                    # 溯源查询
                    from app.core.neo4j import driver as neo4j_driver
                    from app.services.graph import trace_pollution

                    reservoir = await db.get(Reservoir, alert.reservoir_id)
                    try:
                        trace_result = await trace_pollution(
                            neo4j_driver, reservoir.code
                        )
                        trace_info = json.dumps(
                            {
                                "nodes": [n.model_dump() for n in trace_result.nodes],
                                "sources": [
                                    s.model_dump() for s in trace_result.sources
                                ],
                            },
                            ensure_ascii=False,
                        )
                    except Exception as exc:
                        logger.error(f"溯源查询异常: {exc}", exc_info=True)
                        trace_info = ""

                    # 处置备注
                    notes = alert.notes or []
                    process_detail = json.dumps(
                        sorted(notes, key=lambda x: x.get("created_at", "")),
                        ensure_ascii=False,
                    )

                    # 前后 12h 监测记录
                    event_records = (
                        await db.execute(
                            select(
                                MonitoringRecord.indicator_id,
                                MonitoringRecord.value,
                                MonitoringRecord.record_time,
                            )
                            .where(
                                MonitoringRecord.reservoir_id == alert.reservoir_id,
                                MonitoringRecord.record_time
                                >= alert.detected_at - timedelta(hours=12),
                                MonitoringRecord.record_time
                                <= alert.detected_at + timedelta(hours=12),
                            )
                            .order_by(MonitoringRecord.record_time.asc())
                            .limit(200)
                        )
                    ).all()
                    if event_records:
                        data = {
                            "reservoir_id": alert.reservoir_id,
                            "records": [
                                {
                                    "indicator_id": r.indicator_id,
                                    "value": r.value,
                                    "record_time": r.record_time.isoformat(),
                                }
                                for r in event_records
                            ],
                        }
                        process_detail = json.dumps(
                            {
                                "notes": json.loads(process_detail),
                                "monitoring_records": data["records"],
                            },
                            ensure_ascii=False,
                        )

            has_data = bool(patrol_summary or alert_stats)
            if not has_data and report_type in (ReportType.DAILY, ReportType.QUARTERLY):
                logger.info(f"collect_report_data 完成 → 无数据 ({report_type})")
                return {
                    "has_data": False,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                }

            logger.info(
                f"collect_report_data 完成 → patrol={patrol_summary is not None}, alert={alert_stats is not None}"
            )
            return {
                "has_data": True,
                "patrol_summary": patrol_summary,
                "alert_stats": alert_stats,
                "indicator_stats": indicator_stats,
                "analysis_summary": analysis_summary,
                "monthly_trend": monthly_trend,
                "period_comparison": period_comparison,
                "trace_info": trace_info,
                "process_detail": process_detail,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            }

    except Exception as exc:
        logger.error(f"collect_report_data 异常: {exc}", exc_info=True)
        return {
            "has_data": False,
            "error": "系统内部错误",
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
        }


async def llm_generate_report(report_type, data, period_start, period_end):
    """调用 LLM 生成结构化报告内容"""
    if not report_type:
        return

    try:
        prompt_vars = schemas_report.ReportPromptItem(
            period_start=period_start or "",
            period_end=period_end or "",
            patrol_summary=data.get("patrol_summary"),
            alert_stats=data.get("alert_stats"),
            indicator_stats=data.get("indicator_stats"),
            analysis_reference=data.get("analysis_summary"),
            monthly_trend=data.get("monthly_trend"),
            period_comparison=data.get("period_comparison"),
            alert_title=(data.get("alert_stats") or {}).get("title", ""),
            alert_level=str((data.get("alert_stats") or {}).get("alert_level", "")),
            detected_at=(data.get("alert_stats") or {}).get("detected_at", ""),
            alert_status=str((data.get("alert_stats") or {}).get("status", "")),
            indicators_detail=(data.get("alert_stats") or {}).get("indicators"),
            trace_info=data.get("trace_info", ""),
            suggestion_detail=(data.get("alert_stats") or {}).get("suggestion"),
            process_detail=data.get("process_detail", ""),
        )

        system_prompt = PromptTemplate.from_template(
            get_prompt.report[report_type.upper()]["SYSTEM"]
        ).format()

        user_prompt = PromptTemplate.from_template(
            get_prompt.report[report_type.upper()]["USER"]
        ).format(**prompt_vars.model_dump())

        model = get_model.build_chat_model(thinking=False)
        chain = model | JsonOutputParser()
        output = await chain.ainvoke(
            [
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ]
        )

        logger.info(f"llm_generate_report 完成 → 报告标题: {output.get('title', '')}")
        return output

    except Exception as exc:
        logger.error(f"llm_generate_report 异常: {exc}", exc_info=True)


async def save_report(
    report_type, period_start, period_end, llm_output=None, error=None
):
    """将报告写入数据库"""
    now = datetime.now()
    try:
        if error:
            report_status = "draft"
            title = (
                f"{report_type.value if report_type else 'unknown'}报告-{now.strftime('%Y%m%d')}"
                if report_type
                else "未知报告"
            )
            summary, sections, conclusion = None, None, None
        elif llm_output:
            report_status = "draft"
            title = llm_output.get(
                "title",
                f"{report_type.value if report_type else 'unknown'}报告-{now.strftime('%Y%m%d')}",
            )
            summary = llm_output.get("summary")
            sections = llm_output.get("sections")
            conclusion = llm_output.get("conclusion")
        else:
            report_status = "no_data"
            title = (
                f"{report_type.value if report_type else 'unknown'}报告-{now.strftime('%Y%m%d')}"
                if report_type
                else "未知报告"
            )
            summary, sections, conclusion = None, None, None

        period_start_dt = datetime.fromisoformat(period_start) if period_start else now
        period_end_dt = datetime.fromisoformat(period_end) if period_end else now

        async with get_background_db_session() as db:
            report_entry = models_report(
                title=title,
                report_type=report_type.value if report_type else "unknown",
                status=report_status,
                summary=summary,
                sections=sections,
                conclusion=conclusion,
                period_start=period_start_dt,
                period_end=period_end_dt,
            )
            db.add(report_entry)
            await commit_or_rollback(db)
            await db.refresh(report_entry)

            logger.info(
                f"save_report 完成 → report_id={report_entry.id}, type={report_type}, status={report_status}"
            )
            return report_entry.id

    except Exception as exc:
        logger.error(f"save_report 异常: {exc}")


async def run_report_generator(report_type="daily", reservoir_ids=None, alert_id=None):
    """报告生成入口：每天 8:00 或手动触发"""
    if report_type not in ("daily", "quarterly", "event"):
        logger.error(f"非法 report_type: {report_type}")
        return

    try:
        data = await collect_report_data(ReportType(report_type), alert_id)

        if not data.get("has_data", False):
            return await save_report(
                ReportType(report_type),
                data.get("period_start"),
                data.get("period_end"),
                None,
            )

        llm_result = await llm_generate_report(
            ReportType(report_type),
            data,
            data.get("period_start"),
            data.get("period_end"),
        )
        return await save_report(
            ReportType(report_type),
            data.get("period_start"),
            data.get("period_end"),
            llm_result,
        )

    except Exception as exc:
        logger.error(f"报告生成异常: {exc}", exc_info=True)


async def background_generate(report_id, report_type, reservoir_ids, alert_id):
    try:
        await run_report_generator(report_type, reservoir_ids, alert_id)
    except Exception as exc:
        logger.error(f"后台报告生成异常: report_id={report_id}", exc_info=True)
        try:
            async with get_background_db_session() as db:
                entity = await db.get(models_report.Report, report_id)
                if entity and entity.status == "generating":
                    entity.status = "failed"
                    await commit_or_rollback(db)
        except Exception as inner_exc:
            logger.error(f"标记报告失败状态异常: report_id={report_id}", exc_info=True)
