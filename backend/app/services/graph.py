"""图谱查询服务"""

from app.schemas.graph import (
    GetGraphOverviewNodeItem,
    GetGraphOverviewEdgeItem,
    GetGraphOverviewResponse,
)
from app.utils.logger_config import setup_logger
from neo4j import AsyncDriver

logger = setup_logger(__name__)


def _node_id(node_type: str, node) -> str:
    """构建节点复合 ID"""
    key = node.get("code") or node.get("name")
    return f"{node_type.lower()}:{key}"


async def get_graph_overview(session: AsyncDriver, reservoir_code: str | None = None):
    """获取图谱全局概览"""
    nodes = []
    edges = []

    result = await session.run("MATCH (n) RETURN n, labels(n)[0] AS nodeType")
    async for record in result:
        n = record["n"]
        node_type = record["nodeType"]
        node_id = _node_id(node_type, n)
        nodes.append(
            GetGraphOverviewNodeItem(
                id=node_id,
                name=n.get("name"),
                type=node_type,
                code=n.get("code"),
                watershed=n.get("watershed"),
                water_grade=n.get("waterGrade"),
                risk_level=n.get("risk_level"),
                subtype=n.get("type"),
            )
        )

    result = await session.run(
        "MATCH (a)-[r]->(b) "
        "RETURN a, labels(a)[0] AS sourceType, "
        "       b, labels(b)[0] AS targetType, "
        "       type(r) AS relType"
    )
    async for record in result:
        source_id = _node_id(record["sourceType"], record["a"])
        target_id = _node_id(record["targetType"], record["b"])
        edges.append(
            GetGraphOverviewEdgeItem(
                source=source_id,
                target=target_id,
                relation=record["relType"],
            )
        )

    return GetGraphOverviewResponse(nodes=nodes, edges=edges)
