"""图谱管理路由（河流/污染源 CRUD）"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Body
from neo4j import AsyncDriver

from app.core.neo4j import get_neo4j_session
from app.core.security import require_role
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas import graph_admin as schemas_graph_admin
from app.schemas.response import success, error
from app.services import graph_admin as services_graph_admin
from app.utils.exception import ServiceException

router = APIRouter(prefix="/api/v1/graph/admin", tags=["图谱管理"])


@router.post(
    "/rivers/create",
    response_model=ApiResponse[schemas_graph_admin.GetRiverDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="创建河流",
)
async def create_river(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    body: Annotated[schemas_graph_admin.CreateRiverRequest, Body(..., description="创建河流请求参数")],
):
    """创建河流"""
    try:
        result = await services_graph_admin.create_river(neo4j_driver, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/rivers/list",
    response_model=ApiResponse[PaginatedResponse[schemas_graph_admin.GetRiverListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取河流列表，分页返回",
)
async def get_river_list(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    watershed: Annotated[str | None, Query(description="流域筛选")] = None,
):
    """获取河流列表"""
    try:
        result = await services_graph_admin.get_river_list(
            neo4j_driver, page, page_size, watershed
        )
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/rivers/{name}",
    response_model=ApiResponse[schemas_graph_admin.GetRiverDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取河流详情",
)
async def get_river_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="河流名称")],
):
    """获取河流详情"""
    try:
        result = await services_graph_admin.get_river_detail(neo4j_driver, name)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/rivers/{name}",
    response_model=ApiResponse[schemas_graph_admin.GetRiverDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="更新河流",
)
async def update_river(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="河流名称")],
    body: Annotated[schemas_graph_admin.UpdateRiverRequest, Body(..., description="更新河流请求参数")],
):
    """更新河流"""
    try:
        result = await services_graph_admin.update_river(neo4j_driver, name, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/rivers/{name}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除河流",
)
async def delete_river(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="河流名称")],
):
    """删除河流"""
    try:
        result = await services_graph_admin.delete_river(neo4j_driver, name)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/pollution-sources/create",
    response_model=ApiResponse[schemas_graph_admin.GetPollutionSourceDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="创建污染源",
)
async def create_pollution_source(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    body: Annotated[schemas_graph_admin.CreatePollutionSourceRequest, Body(..., description="创建污染源请求参数")],
):
    """创建污染源"""
    try:
        result = await services_graph_admin.create_pollution_source(neo4j_driver, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/pollution-sources/list",
    response_model=ApiResponse[PaginatedResponse[schemas_graph_admin.GetPollutionSourceListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取污染源列表，分页返回",
)
async def get_pollution_source_list(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    source_type: Annotated[str | None, Query(description="污染源类型筛选")] = None,
    risk_level: Annotated[str | None, Query(description="风险等级筛选")] = None,
):
    """获取污染源列表"""
    try:
        result = await services_graph_admin.get_pollution_source_list(
            neo4j_driver, page, page_size, source_type, risk_level
        )
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/pollution-sources/{name}",
    response_model=ApiResponse[schemas_graph_admin.GetPollutionSourceDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取污染源详情",
)
async def get_pollution_source_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="污染源名称")],
):
    """获取污染源详情"""
    try:
        result = await services_graph_admin.get_pollution_source_detail(neo4j_driver, name)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/pollution-sources/{name}",
    response_model=ApiResponse[schemas_graph_admin.GetPollutionSourceDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="更新污染源",
)
async def update_pollution_source(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="污染源名称")],
    body: Annotated[schemas_graph_admin.UpdatePollutionSourceRequest, Body(..., description="更新污染源请求参数")],
):
    """更新污染源"""
    try:
        result = await services_graph_admin.update_pollution_source(neo4j_driver, name, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/pollution-sources/{name}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除污染源",
)
async def delete_pollution_source(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    name: Annotated[str, Path(..., description="污染源名称")],
):
    """删除污染源"""
    try:
        result = await services_graph_admin.delete_pollution_source(neo4j_driver, name)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/reservoirs/create",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jReservoirDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="创建水库（Neo4j直写）",
)
async def create_reservoir(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    body: Annotated[schemas_graph_admin.CreateNeo4jReservoirRequest, Body(..., description="创建水库请求参数")],
):
    """创建水库（Neo4j直写）"""
    try:
        result = await services_graph_admin.create_reservoir(neo4j_driver, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/reservoirs/list",
    response_model=ApiResponse[PaginatedResponse[schemas_graph_admin.GetNeo4jReservoirListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取水库列表（Neo4j直写）",
)
async def get_reservoir_list(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    watershed: Annotated[str | None, Query(description="流域筛选")] = None,
):
    """获取水库列表（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_reservoir_list(neo4j_driver, page, page_size, watershed)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/reservoirs/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jReservoirDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取水库详情（Neo4j直写）",
)
async def get_reservoir_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="水库编号")],
):
    """获取水库详情（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_reservoir_detail(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/reservoirs/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jReservoirDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="更新水库（Neo4j直写）",
)
async def update_reservoir(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="水库编号")],
    body: Annotated[schemas_graph_admin.UpdateNeo4jReservoirRequest, Body(..., description="更新水库请求参数")],
):
    """更新水库（Neo4j直写）"""
    try:
        result = await services_graph_admin.update_reservoir(neo4j_driver, code, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/reservoirs/{code}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除水库（Neo4j直写）",
)
async def delete_reservoir(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="水库编号")],
):
    """删除水库（Neo4j直写）"""
    try:
        result = await services_graph_admin.delete_reservoir(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/stations/create",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jStationDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="创建监测站点（Neo4j直写）",
)
async def create_station(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    body: Annotated[schemas_graph_admin.CreateNeo4jStationRequest, Body(..., description="创建监测站点请求参数")],
):
    """创建监测站点（Neo4j直写）"""
    try:
        result = await services_graph_admin.create_station(neo4j_driver, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/stations/list",
    response_model=ApiResponse[PaginatedResponse[schemas_graph_admin.GetNeo4jStationListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取监测站点列表（Neo4j直写）",
)
async def get_station_list(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    station_type: Annotated[str | None, Query(description="站点类型筛选")] = None,
):
    """获取监测站点列表（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_station_list(neo4j_driver, page, page_size, station_type)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/stations/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jStationDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取监测站点详情（Neo4j直写）",
)
async def get_station_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="站点编号")],
):
    """获取监测站点详情（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_station_detail(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/stations/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jStationDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="更新监测站点（Neo4j直写）",
)
async def update_station(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="站点编号")],
    body: Annotated[schemas_graph_admin.UpdateNeo4jStationRequest, Body(..., description="更新监测站点请求参数")],
):
    """更新监测站点（Neo4j直写）"""
    try:
        result = await services_graph_admin.update_station(neo4j_driver, code, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/stations/{code}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除监测站点（Neo4j直写）",
)
async def delete_station(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="站点编号")],
):
    """删除监测站点（Neo4j直写）"""
    try:
        result = await services_graph_admin.delete_station(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/indicators/create",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jIndicatorDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="创建监测指标（Neo4j直写）",
)
async def create_indicator(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    body: Annotated[schemas_graph_admin.CreateNeo4jIndicatorRequest, Body(..., description="创建监测指标请求参数")],
):
    """创建监测指标（Neo4j直写）"""
    try:
        result = await services_graph_admin.create_indicator(neo4j_driver, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/indicators/list",
    response_model=ApiResponse[PaginatedResponse[schemas_graph_admin.GetNeo4jIndicatorListResponse]],
    dependencies=[Depends(require_role("admin"))],
    description="获取监测指标列表（Neo4j直写）",
)
async def get_indicator_list(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: Annotated[str | None, Query(description="分类筛选")] = None,
):
    """获取监测指标列表（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_indicator_list(neo4j_driver, page, page_size, category)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/indicators/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jIndicatorDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="获取监测指标详情（Neo4j直写）",
)
async def get_indicator_detail(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="指标编码")],
):
    """获取监测指标详情（Neo4j直写）"""
    try:
        result = await services_graph_admin.get_indicator_detail(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.put(
    "/indicators/{code}",
    response_model=ApiResponse[schemas_graph_admin.GetNeo4jIndicatorDetailResponse],
    dependencies=[Depends(require_role("admin"))],
    description="更新监测指标（Neo4j直写）",
)
async def update_indicator(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="指标编码")],
    body: Annotated[schemas_graph_admin.UpdateNeo4jIndicatorRequest, Body(..., description="更新监测指标请求参数")],
):
    """更新监测指标（Neo4j直写）"""
    try:
        result = await services_graph_admin.update_indicator(neo4j_driver, code, body)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)


@router.delete(
    "/indicators/{code}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_role("admin"))],
    description="删除监测指标（Neo4j直写）",
)
async def delete_indicator(
    neo4j_driver: Annotated[AsyncDriver, Depends(get_neo4j_session)],
    code: Annotated[str, Path(..., description="指标编码")],
):
    """删除监测指标（Neo4j直写）"""
    try:
        result = await services_graph_admin.delete_indicator(neo4j_driver, code)
        return success(data=result)
    except ServiceException as e:
        return error(e.code, e.message)
