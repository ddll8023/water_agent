"""M4 智能问答 ReAct Agent 工具集"""

import json

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_background_db_session
from app.core.neo4j import driver as neo4j_driver
from app.models.indicator import Indicator
from app.services.graph import trace_pollution, search_node, get_node_expand, get_node_detail
from app.utils.logger_config import setup_logger
from app.utils.model_factory import get_model
from app.utils.prompt_factory import get_prompt
from app.utils.retriever import ensemble_retrieve
from app.schemas.graph import SearchNodeRequest, GetNodeDetailResponse

logger = setup_logger(__name__)


@tool
async def search_knowledge_base_tool(query: str = "", top_k: int = 5, doc_type: str | None = None) -> str:
    """从知识库检索与 query 相关的文档片段。doc_type 可选值：standard / case / sop"""
    try:
        docs = await ensemble_retrieve(query, top_k=top_k, doc_type=doc_type)
        if not docs:
            return json.dumps({"success": True, "data": "知识库中未找到相关文档"}, ensure_ascii=False)
        content = "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)])
        return json.dumps({"success": True, "data": content}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"search_knowledge_base_tool 异常: {e}", exc_info=True)
        return json.dumps({"success": False, "error": f"知识库检索失败: {e}"}, ensure_ascii=False)


@tool
async def query_monitoring_data_tool(description: str = "") -> str:
    """根据自然语言描述查询 MySQL 监测数据。生成 SQL 执行后返回 JSON。"""
    db = get_background_db_session()
    try:
        system_prompt = PromptTemplate.from_template(
            get_prompt.chat_agent["SQL_GENERATION"]["SYSTEM"]
        ).format()
        user_prompt = PromptTemplate.from_template(
            get_prompt.chat_agent["SQL_GENERATION"]["USER"]
        ).format(query=description)
        messages = [SystemMessage(system_prompt), HumanMessage(user_prompt)]
        model = get_model.build_chat_model(thinking=False)
        sql_result = await model.ainvoke(messages)
        sql = sql_result.content.strip()
        rows = (await db.execute(text(sql))).all()
        result = [dict(r._mapping) for r in rows]
        if result:
            return json.dumps({"success": True, "data": result}, ensure_ascii=False, default=str)
        return json.dumps({"success": True, "data": "未查询到数据"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"query_monitoring_data_tool 异常: {e}", exc_info=True)
        return json.dumps({"success": False, "error": f"数据查询失败: {e}"}, ensure_ascii=False)
    finally:
        await db.close()


@tool
async def query_knowledge_graph_tool(
    template: str = "",
    keyword: str = "",
    node_type: str = "",
    node_id: str = "",
    reservoir_code: str = "",
) -> str:
    """使用预定义模板查询知识图谱。可用模板与参数：
    - trace_pollution: 需 reservoir_code
    - search_node: 需 keyword，可选 node_type
    - expand_node: 需 node_type + node_id
    - node_detail: 需 node_type + node_id"""
    try:
        async with neo4j_driver.session() as session:
            if template == "trace_pollution":
                if not reservoir_code:
                    return json.dumps({"success": False, "error": "请提供水库编码"}, ensure_ascii=False)
                result = await trace_pollution(session, reservoir_code)
                return json.dumps({"success": True, "data": str(result.model_dump())}, ensure_ascii=False)

            elif template == "search_node":
                if not keyword:
                    return json.dumps({"success": False, "error": "请提供搜索关键词"}, ensure_ascii=False)
                req = SearchNodeRequest(keyword=keyword, type=node_type or None)
                result = await search_node(session, req)
                return json.dumps({"success": True, "data": str(result.model_dump())}, ensure_ascii=False)

            elif template == "expand_node":
                if not node_type or not node_id:
                    return json.dumps({"success": False, "error": "请提供节点类型和节点ID"}, ensure_ascii=False)
                result = await get_node_expand(session, node_type, node_id)
                return json.dumps({"success": True, "data": str(result.model_dump())}, ensure_ascii=False)

            elif template == "node_detail":
                if not node_type or not node_id:
                    return json.dumps({"success": False, "error": "请提供节点类型和节点ID"}, ensure_ascii=False)
                result = await get_node_detail(session, node_type, node_id)
                if result:
                    return json.dumps({"success": True, "data": str(result.model_dump())}, ensure_ascii=False)
                return json.dumps({"success": True, "data": "未找到节点"}, ensure_ascii=False)

            else:
                return json.dumps({"success": False, "error": f"未知模板：{template}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"query_knowledge_graph_tool 异常: template={template}, {e}", exc_info=True)
        return json.dumps({"success": False, "error": f"图谱查询失败: {e}"}, ensure_ascii=False)


@tool
async def check_water_standard_tool(indicator_name: str = "") -> str:
    """查询指定水质指标的国家标准限值（Ⅰ~Ⅴ类上下限）。"""
    db = get_background_db_session()
    try:
        stmt = select(Indicator).where(Indicator.name.like(f"%{indicator_name}%"))
        result = (await db.scalars(stmt)).first()
        if not result:
            stmt = select(Indicator).where(Indicator.code.like(f"%{indicator_name}%"))
            result = (await db.scalars(stmt)).first()
        if not result:
            return json.dumps({"success": True, "data": f"未找到指标: {indicator_name}"}, ensure_ascii=False)
        return json.dumps({"success": True, "data": _build_standard_response(result)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"check_water_standard_tool 异常: {e}", exc_info=True)
        return json.dumps({"success": False, "error": f"标准查询失败: {e}"}, ensure_ascii=False)
    finally:
        await db.close()


"""辅助函数"""


def _build_standard_response(indicator: Indicator) -> str:
    """构建标准限值查询响应文本"""
    lines = [f"指标：{indicator.name}（{indicator.code}）"]
    if indicator.unit:
        lines.append(f"单位：{indicator.unit}")
    if indicator.category:
        lines.append(f"分类：{indicator.category}")

    class_grades = [
        ("Ⅰ类", indicator.standard_limit_i_lower, indicator.standard_limit_i_upper),
        ("Ⅱ类", indicator.standard_limit_ii_lower, indicator.standard_limit_ii_upper),
        ("Ⅲ类", indicator.standard_limit_iii_lower, indicator.standard_limit_iii_upper),
        ("Ⅳ类", indicator.standard_limit_iv_lower, indicator.standard_limit_iv_upper),
        ("Ⅴ类", indicator.standard_limit_v_lower, indicator.standard_limit_v_upper),
    ]
    lines.append("标准限值：")
    for grade, lower, upper in class_grades:
        lower_str = f"下限={lower}" if lower is not None else ""
        upper_str = f"上限={upper}" if upper is not None else ""
        range_str = " ~ ".join(filter(None, [lower_str, upper_str]))
        if range_str:
            lines.append(f"  {grade}：{range_str}")
    return "\n".join(lines)
