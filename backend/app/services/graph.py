"""图谱查询服务"""

from app.schemas.graph import (
    GetGraphOverviewNodeItem,
    GetGraphOverviewEdgeItem,
    GetGraphOverviewResponse,
    GetNodeDetailResponse,
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


async def get_node_detail(
    neo4j_driver: AsyncDriver, node_type: str, node_id: str
):
    """获取节点详情"""
    query = """
        MATCH (n)
        WHERE toLower(labels(n)[0]) = $node_type
          AND (n.code = $node_id OR n.name = $node_id)
        RETURN n, labels(n)[0] AS nodeType
    """
    result = await neo4j_driver.run(query, node_type=node_type.lower(), node_id=node_id)
    record = await result.single()
    if not record:
        return None

    n = record["n"]
    attributes = {}
    for key in n:
        if key.startswith("_"):
            continue
        attributes[key] = str(n.get(key)) if n.get(key) is not None else None

    return GetNodeDetailResponse(
        id=_node_id(record["nodeType"], n),
        name=n.get("name"),
        type=record["nodeType"],
        attributes=attributes,
    )


async def get_node_expand(
    neo4j_driver: AsyncDriver, node_type: str, node_id: str
):
    """节点一跳扩展"""
    nodes = []
    edges = []

    node_query = """
        MATCH (n)-[r]-(connected)
        WHERE toLower(labels(n)[0]) = $node_type
          AND (n.code = $node_id OR n.name = $node_id)
        RETURN DISTINCT connected, labels(connected)[0] AS nodeType
    """
    result = await neo4j_driver.run(node_query, node_type=node_type.lower(), node_id=node_id)
    async for record in result:
        connected = record["connected"]
        node_label = record["nodeType"]
        nodes.append(
            GetGraphOverviewNodeItem(
                id=_node_id(node_label, connected),
                name=connected.get("name"),
                type=node_label,
                code=connected.get("code"),
                watershed=connected.get("watershed"),
                water_grade=connected.get("waterGrade"),
                risk_level=connected.get("risk_level"),
                subtype=connected.get("type"),
            )
        )

    edge_query = """
        MATCH (n)-[r]-(connected)
        WHERE toLower(labels(n)[0]) = $node_type
          AND (n.code = $node_id OR n.name = $node_id)
        RETURN DISTINCT n, labels(n)[0] AS sourceType,
               connected, labels(connected)[0] AS targetType,
               type(r) AS relType
    """
    result = await neo4j_driver.run(edge_query, node_type=node_type.lower(), node_id=node_id)
    async for record in result:
        source_id = _node_id(record["sourceType"], record["n"])
        target_id = _node_id(record["targetType"], record["connected"])
        edges.append(
            GetGraphOverviewEdgeItem(
                source=source_id,
                target=target_id,
                relation=record["relType"],
            )
        )

    return schemas_graph.GetGraphExpandResponse(nodes=nodes, edges=edges)


async def trace_pollution(
    neo4j_driver: AsyncDriver, reservoir_code: str
):
    """污染溯源路径查询"""
    node_query = """
        MATCH path = (ps:PollutionSource)-[d:DISCHARGES_INTO]->(river:River)-[f:FLOWS_INTO]->(res:Reservoir {code: $code})
        WITH nodes(path) AS path_nodes
        UNWIND path_nodes AS n
        RETURN DISTINCT n, labels(n)[0] AS nodeType
    """
    result = await neo4j_driver.run(node_query, code=reservoir_code)
    nodes = []
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

    if not nodes:
        return schemas_graph.GetTracePollutionResponse(nodes=[], edges=[], sources=[])

    edge_query = """
        MATCH path = (ps:PollutionSource)-[d:DISCHARGES_INTO]->(river:River)-[f:FLOWS_INTO]->(res:Reservoir {code: $code})
        WITH relationships(path) AS path_rels
        UNWIND path_rels AS r
        RETURN DISTINCT startNode(r) AS a, labels(startNode(r))[0] AS sourceType,
               endNode(r) AS b, labels(endNode(r))[0] AS targetType,
               type(r) AS relType
    """
    result = await neo4j_driver.run(edge_query, code=reservoir_code)
    edges = []
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

    source_query = """
        MATCH (ps:PollutionSource)-[d:DISCHARGES_INTO]->(river:River)-[f:FLOWS_INTO]->(res:Reservoir {code: $code})
        RETURN ps.name AS name, ps.risk_level AS risk_level,
               d.distance_km AS distance_km, ps.violation_count AS violation_count
        ORDER BY d.distance_km ASC, ps.violation_count DESC
    """
    result = await neo4j_driver.run(source_query, code=reservoir_code)
    sources = []
    async for record in result:
        ps = record
        sources.append(
            schemas_graph.TraceSourceItem(
                id=_node_id("pollutionsource", {"code": None, "name": ps["name"]}),
                name=ps["name"],
                risk_level=ps["risk_level"],
                distance_km=ps["distance_km"],
                violation_count=ps["violation_count"],
            )
        )

    return schemas_graph.GetTracePollutionResponse(nodes=nodes, edges=edges, sources=sources)
