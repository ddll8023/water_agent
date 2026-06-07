"""图谱路由"""

from fastapi import APIRouter, Query, Depends
from typing import Annotated

from app.schemas.response import success, error
from app.schemas.common import ApiResponse
from app.schemas import graph as schemas_grapg
from app.core.neo4j import get_neo4j_session
from app.utils.exception import ServiceException
from app.services import graph as services_graph
from app.core.security import require_role
from neo4j import AsyncDriver

router = APIRouter(prefix="/api/v1/graph", tags=["知识图谱"])


@router.get(
    "/overview",
    response_model=ApiResponse[schemas_grapg.GetGraphOverviewResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    description="获取图谱全局概览",
)
async def get_graph_overview(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    reservoir_code: Annotated[str | None, Query(description="水库编号")] = None,
):
    """获取图谱全局概览"""
    try:
        result = await services_graph.get_graph_overview(neo4j_driver, reservoir_code)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/search",
    response_model=ApiResponse[schemas_grapg.SearchNodeResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    description="搜索节点",
)
async def search_node(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    search_node_request: Annotated[schemas_grapg.SearchNodeRequest, Query()],
):
    """搜索节点"""

    try:
        result = await services_graph.search_node(neo4j_driver, search_node_request)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)


@router.get(
    "/node/{node_type}/{node_id}",
    response_model=ApiResponse[schemas_grapg.GetNodeDetailResponse],
    dependencies=[Depends(require_role("admin", "user"))],
    description="获取节点详情",
)
async def get_node_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    node_type: str,
    node_id: str,
):
    """获取节点详情"""
    try:
        result = await services_graph.get_node_detail(neo4j_driver, node_type, node_id)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
