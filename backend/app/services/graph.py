"""图谱查询服务"""

from app.schemas.graph import (
    GetGraphOverviewNodeItem,
    GetGraphOverviewEdgeItem,
    GetGraphOverviewResponse,
)
from app.utils.logger_config import setup_logger
from neo4j import AsyncDriver
from app.schemas import graph as schemas_graph

logger = setup_logger(__name__)


def _node_id(node_type: str, node) -> str:
    """构建节点复合 ID"""
    key = node.get("code") or node.get("name")
    return f"{node_type.lower()}:{key}"


async def get_graph_overview(
    neo4j_driver: AsyncDriver, reservoir_code: str | None = None
):
    """获取图谱全局概览"""
    nodes = []
    edges = []

    if reservoir_code:
        node_query = """
            MATCH (res:Reservoir {code: $code})
            OPTIONAL MATCH (river:River)-[:FLOWS_INTO]->(res)
            OPTIONAL MATCH (ps:PollutionSource)-[:DISCHARGES_INTO]->(river)
            WITH COLLECT(DISTINCT res) + COLLECT(DISTINCT river) + COLLECT(DISTINCT ps) AS connected
            MATCH (ind:Indicator)
            WITH connected, COLLECT(ind) AS indicators
            MATCH (ms:MonitoringStation)
            WITH connected, indicators, COLLECT(ms) AS stations
            WITH connected + indicators + stations AS all_nodes
            UNWIND all_nodes AS n
            WITH DISTINCT n
            WHERE n IS NOT NULL
            RETURN n, labels(n)[0] AS nodeType
        """
        params = {"code": reservoir_code}
    else:
        node_query = "MATCH (n) RETURN n, labels(n)[0] AS nodeType"
        params = {}

    result = await neo4j_driver.run(node_query, **params)
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

    if reservoir_code:
        edge_query = """
            MATCH (res:Reservoir {code: $code})
            OPTIONAL MATCH (river:River)-[:FLOWS_INTO]->(res)
            OPTIONAL MATCH (ps:PollutionSource)-[:DISCHARGES_INTO]->(river)
            WITH COLLECT(DISTINCT res) + COLLECT(DISTINCT river) + COLLECT(DISTINCT ps) AS connected
            MATCH (ind:Indicator)
            WITH connected, COLLECT(ind) AS indicators
            MATCH (ms:MonitoringStation)
            WITH connected, indicators, COLLECT(ms) AS stations
            UNWIND connected + indicators + stations AS n
            WITH COLLECT(DISTINCT elementId(n)) AS node_ids
            MATCH (a)-[r]->(b)
            WHERE elementId(a) IN node_ids AND elementId(b) IN node_ids
            RETURN a, labels(a)[0] AS sourceType,
                   b, labels(b)[0] AS targetType,
                   type(r) AS relType
        """
    else:
        edge_query = """
            MATCH (a)-[r]->(b)
            RETURN a, labels(a)[0] AS sourceType,
                   b, labels(b)[0] AS targetType,
                   type(r) AS relType
        """

    result = await neo4j_driver.run(edge_query, **params)
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


async def search_node(
    neo4j_driver: AsyncDriver, search_node_request: schemas_graph.SearchNodeRequest
):
    """搜索节点"""
    query = """
        MATCH (n)
        WHERE n.name CONTAINS $keyword OR n.code CONTAINS $keyword
        RETURN n, labels(n)[0] AS nodeType
    """
    result = await neo4j_driver.run(query, keyword=search_node_request.keyword)
    node_list = []
    async for record in result:
        n = record["n"]
        node_type = record["nodeType"]
        node_list.append(
            GetGraphOverviewNodeItem(
                id=_node_id(node_type, n),
                name=n.get("name"),
                type=node_type,
                code=n.get("code"),
                watershed=n.get("watershed"),
                water_grade=n.get("waterGrade"),
                risk_level=n.get("risk_level"),
                subtype=n.get("type"),
            )
        )
    return schemas_graph.SearchNodeResponse(node_list=node_list)
