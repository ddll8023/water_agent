"""图谱路由"""

from fastapi import APIRouter, Query, Depends
from typing import Annotated

from app.schemas.response import success, error
from app.schemas.common import ApiResponse
from app.schemas.graph import GetGraphOverviewResponse
from app.core.neo4j import get_neo4j_session
from app.utils.exception import ServiceException
from app.services import graph as services_graph

router = APIRouter(prefix="/api/v1/graph", tags=["知识图谱"])


@router.get(
    "/overview",
    response_model=ApiResponse[GetGraphOverviewResponse],
    description="获取图谱全局概览",
)
async def get_graph_overview(
    reservoir_code: Annotated[str | None, Query(description="水库编号")] = None,
    session=Depends(get_neo4j_session),
):
    """获取图谱全局概览"""
    try:
        result = await services_graph.get_graph_overview(session, reservoir_code)
        return success(data=result)
    except ServiceException as e:
        return error(code=e.code, message=e.message)
