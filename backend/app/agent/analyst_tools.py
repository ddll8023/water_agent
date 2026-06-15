"""Analyst Agent ReAct 工具集"""

from datetime import datetime, timedelta

from async_lru import alru_cache
from langchain_core.tools import tool
from sqlalchemy import select

from app.core.database import get_background_db_session
from app.core.neo4j import driver as neo4j_driver
from app.models.reservoir import Reservoir
from app.schemas.monitorings import GetMonitoringRecordsTrendRequest
from app.services.graph import trace_pollution
from app.services.monitoring import get_monitoring_records_trend
from app.utils.logger_config import setup_logger
from app.utils.retriever import ensemble_retrieve

logger = setup_logger(__name__)


@tool
async def query_reservoir_overview_tool(reservoir_ids: list[int] | None = None) -> str:
    """查询所有或指定水库的基本信息（名称、等级、流域等）。
    第1步调用一次，获取全局概览后按水库编号逐个深入。"""
    try:
        async with get_background_db_session() as db:
            stmt = select(Reservoir)
            if reservoir_ids:
                stmt = stmt.where(Reservoir.id.in_(reservoir_ids))
            result = (await db.scalars(stmt)).all()
            if not result:
                return "无可用水库数据"
            lines = [
                f"{r.id}:{r.name}(code={r.code},grade={r.water_grade},basin={r.watershed})"
                for r in result
            ]
            return "水库列表:\n" + "\n".join(lines)
    except Exception as e:
        logger.error(f"query_reservoir_overview_tool 异常: {e}")
        return f"查询失败: {e}"


@tool
async def query_monitoring_records_tool(
    reservoir_id: int,
    indicator_ids: list[int] | None = None,
    hours: int = 6,
) -> str:
    """查询指定水库最近 N 小时的监测数据并计算趋势特征。
    对同一 reservoir_id 的重复查询自动命中缓存。"""
    try:
        reservoir_id = int(reservoir_id)
        hours = min(max(hours, 1), 168)
        return await _cached_monitoring_query(reservoir_id, hours)
    except Exception as e:
        logger.error(
            f"query_monitoring_records_tool 异常: reservoir_id={reservoir_id}, {e}"
        )
        return f"查询失败: {e}"


@alru_cache(maxsize=64)
async def _cached_monitoring_query(
    reservoir_id: int,
    hours: int,
) -> str:
    """实际查库 + 计算趋势特征（自动缓存）"""

    async with get_background_db_session() as db:
        request = GetMonitoringRecordsTrendRequest(
            reservoir_id=reservoir_id,
            start_time=(datetime.now() - timedelta(hours=hours)).isoformat(),
            end_time=datetime.now().isoformat(),
        )
        result = await get_monitoring_records_trend(db, request)
        return str(result.model_dump())


@tool
async def neo4j_trace_pollution_tool(reservoir_code: str) -> str:
    """查询指定水库的上游污染源溯源信息。
    返回污染源列表（含距离、风险等级、违规次数）。"""
    try:
        async with neo4j_driver.session() as session:
            result = await trace_pollution(session, reservoir_code)
            return str(result.model_dump())
    except Exception as e:
        logger.error(f"neo4j_trace_pollution_tool 异常: code={reservoir_code}, {e}")
        return f"溯源查询失败: {e}"


@tool
async def rag_retrieve_context_tool(query: str, top_k: int = 5) -> str:
    """从知识库检索与 query 相关的文档片段。
    用于分析后期获取标准规范、历史案例等参考信息。"""
    try:
        docs = await ensemble_retrieve(query, top_k=top_k)
        if not docs:
            return "知识库中未找到相关文档"
        return "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)])
    except Exception as e:
        logger.error(f"rag_retrieve_context_tool 异常: {e}")
        return f"知识库检索失败: {e}"
