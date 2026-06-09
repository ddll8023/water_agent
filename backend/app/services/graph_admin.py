"""河流与污染源管理服务"""

import math

from neo4j import AsyncDriver

from app.schemas.common import PaginatedResponse, PaginationInfo, ErrorCode
from app.schemas import graph_admin as schemas_graph_admin
from app.utils.exception import ServiceException


async def create_river(driver: AsyncDriver, request: schemas_graph_admin.CreateRiverRequest):
    """创建河流"""
    await driver.run(
        """MERGE (r:River {name: $name})
           ON CREATE SET r.length = $length, r.watershed = $watershed""",
        name=request.name, length_km=request.length, watershed=request.watershed,
    )

    if request.flows_into_reservoir_code:
        await driver.run(
            """MATCH (r:River {name: $name})
               MATCH (res:Reservoir {code: $code})
               MERGE (r)-[:FLOWS_INTO]->(res)""",
            name=request.name, code=request.flows_into_reservoir_code,
        )

    return schemas_graph_admin.GetRiverDetailResponse(
        name=request.name,
        length_km=request.length,
        watershed=request.watershed,
        flows_into_reservoir_code=request.flows_into_reservoir_code,
    )


async def get_river_list(
    driver: AsyncDriver, page: int, page_size: int, watershed: str | None = None
):
    """获取河流列表"""
    count_params = {}
    count_where = ""
    if watershed:
        count_where = "WHERE r.watershed = $watershed"
        count_params["watershed"] = watershed

    count_result = await driver.run(
        f"MATCH (r:River) {count_where} RETURN count(r) AS total",
        **count_params,
    )
    count_record = await count_result.single()
    total = count_record["total"] if count_record else 0

    list_params = {"skip": (page - 1) * page_size, "limit": page_size}
    list_where = ""
    if watershed:
        list_where = "WHERE r.watershed = $watershed"
        list_params["watershed"] = watershed

    list_result = await driver.run(
        f"""MATCH (r:River) {list_where}
            OPTIONAL MATCH (r)-[f:FLOWS_INTO]->(res:Reservoir)
            RETURN r.name AS name, r.length AS length,
                   r.watershed AS watershed, res.code AS flows_into_reservoir_code
            SKIP $skip LIMIT $limit""",
        **list_params,
    )

    items = []
    async for record in list_result:
        items.append(
            schemas_graph_admin.GetRiverListResponse(
                name=record["name"],
                length_km=record.get("length"),
                watershed=record.get("watershed"),
                flows_into_reservoir_code=record.get("flows_into_reservoir_code"),
            )
        )

    return PaginatedResponse(
        lists=items,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


async def get_river_detail(driver: AsyncDriver, name: str):
    """获取河流详情"""
    result = await driver.run(
        """MATCH (r:River {name: $name})
           OPTIONAL MATCH (r)-[f:FLOWS_INTO]->(res:Reservoir)
           RETURN r.name AS name, r.length AS length,
                  r.watershed AS watershed, res.code AS flows_into_reservoir_code""",
        name=name,
    )
    record = await result.single()
    if not record:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "河流不存在")

    return schemas_graph_admin.GetRiverDetailResponse(
        name=record["name"],
        length_km=record.get("length"),
        watershed=record.get("watershed"),
        flows_into_reservoir_code=record.get("flows_into_reservoir_code"),
    )


async def update_river(driver: AsyncDriver, name: str, request: schemas_graph_admin.UpdateRiverRequest):
    """更新河流"""
    check = await driver.run("MATCH (r:River {name: $name}) RETURN r", name=name)
    if not await check.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "河流不存在")

    set_clauses = []
    params = {"name": name}
    if request.length is not None:
        set_clauses.append("r.length = $length")
        params["length"] = request.length
    if request.watershed is not None:
        set_clauses.append("r.watershed = $watershed")
        params["watershed"] = request.watershed

    if set_clauses:
        await driver.run(
            f"MATCH (r:River {{name: $name}}) SET {', '.join(set_clauses)}",
            **params,
        )

    if request.flows_into_reservoir_code is not None:
        await driver.run(
            """MATCH (r:River {name: $name})
               OPTIONAL MATCH (r)-[f:FLOWS_INTO]->()
               DELETE f
               WITH r
               MATCH (res:Reservoir {code: $code})
               MERGE (r)-[:FLOWS_INTO]->(res)""",
            name=name, code=request.flows_into_reservoir_code,
        )

    return await get_river_detail(driver, name)


async def delete_river(driver: AsyncDriver, name: str):
    """删除河流"""
    result = await driver.run(
        "MATCH (r:River {name: $name}) RETURN r", name=name,
    )
    if not await result.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "河流不存在")

    await driver.run("MATCH (r:River {name: $name}) DETACH DELETE r", name=name)
    return True


async def create_pollution_source(driver: AsyncDriver, request: schemas_graph_admin.CreatePollutionSourceRequest):
    """创建污染源"""
    await driver.run(
        """MERGE (p:PollutionSource {name: $name})
           ON CREATE SET p.type = $type, p.longitude = $longitude,
               p.latitude = $latitude, p.risk_level = $risk_level,
               p.violation_count = $violation_count""",
        name=request.name, type=request.type,
        longitude=request.longitude, latitude=request.latitude,
        risk_level=request.risk_level, violation_count=request.violation_count,
    )

    if request.discharges_into_river_name:
        await driver.run(
            """MATCH (p:PollutionSource {name: $pname})
               MATCH (r:River {name: $rname})
               MERGE (p)-[:DISCHARGES_INTO {distance_km: $distance_km}]->(r)""",
            pname=request.name, rname=request.discharges_into_river_name,
            distance_km=request.distance_km,
        )

    return schemas_graph_admin.GetPollutionSourceDetailResponse(
        name=request.name,
        type=request.type,
        longitude=request.longitude,
        latitude=request.latitude,
        risk_level=request.risk_level,
        violation_count=request.violation_count,
        discharges_into_river_name=request.discharges_into_river_name,
        distance_km=request.distance_km,
    )


async def get_pollution_source_list(
    driver: AsyncDriver, page: int, page_size: int,
    source_type: str | None = None, risk_level: str | None = None,
):
    """获取污染源列表"""
    where_clauses = []
    params = {}
    if source_type:
        where_clauses.append("p.type = $type")
        params["type"] = source_type
    if risk_level:
        where_clauses.append("p.risk_level = $risk_level")
        params["risk_level"] = risk_level

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_result = await driver.run(
        f"MATCH (p:PollutionSource) {where_str} RETURN count(p) AS total",
        **params,
    )
    count_record = await count_result.single()
    total = count_record["total"] if count_record else 0

    list_params = {**params, "skip": (page - 1) * page_size, "limit": page_size}
    list_result = await driver.run(
        f"""MATCH (p:PollutionSource) {where_str}
            OPTIONAL MATCH (p)-[d:DISCHARGES_INTO]->(r:River)
            RETURN p.name AS name, p.type AS type,
                   p.longitude AS longitude, p.latitude AS latitude,
                   p.risk_level AS risk_level, p.violation_count AS violation_count,
                   r.name AS discharges_into_river_name, d.distance_km AS distance_km
            SKIP $skip LIMIT $limit""",
        **list_params,
    )

    items = []
    async for record in list_result:
        items.append(
            schemas_graph_admin.GetPollutionSourceListResponse(
                name=record["name"],
                type=record["type"],
                longitude=record["longitude"],
                latitude=record["latitude"],
                risk_level=record["risk_level"],
                violation_count=record["violation_count"],
                discharges_into_river_name=record.get("discharges_into_river_name"),
                distance_km=record.get("distance_km"),
            )
        )

    return PaginatedResponse(
        lists=items,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


async def get_pollution_source_detail(driver: AsyncDriver, name: str):
    """获取污染源详情"""
    result = await driver.run(
        """MATCH (p:PollutionSource {name: $name})
           OPTIONAL MATCH (p)-[d:DISCHARGES_INTO]->(r:River)
           RETURN p.name AS name, p.type AS type,
                  p.longitude AS longitude, p.latitude AS latitude,
                  p.risk_level AS risk_level, p.violation_count AS violation_count,
                  r.name AS discharges_into_river_name, d.distance_km AS distance_km""",
        name=name,
    )
    record = await result.single()
    if not record:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "污染源不存在")

    return schemas_graph_admin.GetPollutionSourceDetailResponse(
        name=record["name"],
        type=record["type"],
        longitude=record["longitude"],
        latitude=record["latitude"],
        risk_level=record["risk_level"],
        violation_count=record["violation_count"],
        discharges_into_river_name=record.get("discharges_into_river_name"),
        distance_km=record.get("distance_km"),
    )


async def update_pollution_source(driver: AsyncDriver, name: str, request: schemas_graph_admin.UpdatePollutionSourceRequest):
    """更新污染源"""
    check = await driver.run(
        "MATCH (p:PollutionSource {name: $name}) RETURN p", name=name,
    )
    if not await check.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "污染源不存在")

    set_clauses = []
    params = {"name": name}

    field_map = {
        "name": "p.name",
        "type": "p.type",
        "longitude": "p.longitude",
        "latitude": "p.latitude",
        "risk_level": "p.risk_level",
        "violation_count": "p.violation_count",
    }
    for field, cypher_field in field_map.items():
        val = getattr(request, field, None)
        if val is not None:
            set_clauses.append(f"{cypher_field} = ${field}")
            params[field] = val

    if set_clauses:
        await driver.run(
            f"MATCH (p:PollutionSource {{name: $name}}) SET {', '.join(set_clauses)}",
            **params,
        )

    if request.discharges_into_river_name is not None:
        await driver.run(
            """MATCH (p:PollutionSource {name: $name})
               OPTIONAL MATCH (p)-[d:DISCHARGES_INTO]->()
               DELETE d
               WITH p
               MATCH (r:River {name: $rname})
               MERGE (p)-[:DISCHARGES_INTO {distance_km: $distance_km}]->(r)""",
            name=name, rname=request.discharges_into_river_name,
            distance_km=request.distance_km,
        )

    return await get_pollution_source_detail(driver, name)


async def delete_pollution_source(driver: AsyncDriver, name: str):
    """删除污染源"""
    result = await driver.run(
        "MATCH (p:PollutionSource {name: $name}) RETURN p", name=name,
    )
    if not await result.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "污染源不存在")

    await driver.run(
        "MATCH (p:PollutionSource {name: $name}) DETACH DELETE p", name=name,
    )
    return True


async def create_reservoir(driver: AsyncDriver, request: schemas_graph_admin.CreateNeo4jReservoirRequest):
    """创建水库（Neo4j直写）"""
    await driver.run(
        """MERGE (n:Reservoir {code: $code})
           ON CREATE SET n.name = $name, n.location = $location,
               n.longitude = $longitude, n.latitude = $latitude,
               n.capacity = $capacity, n.waterGrade = $water_grade,
               n.watershed = $watershed
           ON MATCH SET n.name = $name, n.location = $location,
               n.longitude = $longitude, n.latitude = $latitude,
               n.capacity = $capacity, n.waterGrade = $water_grade,
               n.watershed = $watershed""",
        code=request.code, name=request.name, location=request.location,
        longitude=request.longitude, latitude=request.latitude,
        capacity=request.capacity, water_grade=request.water_grade,
        watershed=request.watershed,
    )
    return schemas_graph_admin.GetNeo4jReservoirDetailResponse(
        code=request.code, name=request.name, location=request.location,
        longitude=request.longitude, latitude=request.latitude,
        capacity=request.capacity, water_grade=request.water_grade,
        watershed=request.watershed,
    )


async def get_reservoir_list(driver: AsyncDriver, page: int, page_size: int, watershed: str | None = None):
    """获取水库列表（Neo4j直写）"""
    count_params = {}
    count_where = ""
    if watershed:
        count_where = "WHERE n.watershed = $watershed"
        count_params["watershed"] = watershed

    count_result = await driver.run(
        f"MATCH (n:Reservoir) {count_where} RETURN count(n) AS total",
        **count_params,
    )
    count_record = await count_result.single()
    total = count_record["total"] if count_record else 0

    list_params = {"skip": (page - 1) * page_size, "limit": page_size}
    list_where = ""
    if watershed:
        list_where = "WHERE n.watershed = $watershed"
        list_params["watershed"] = watershed

    list_result = await driver.run(
        f"""MATCH (n:Reservoir) {list_where}
            RETURN n.code AS code, n.name AS name, n.location AS location,
                   n.longitude AS longitude, n.latitude AS latitude,
                   n.capacity AS capacity, n.waterGrade AS water_grade,
                   n.watershed AS watershed
            SKIP $skip LIMIT $limit""",
        **list_params,
    )

    items = []
    async for record in list_result:
        items.append(schemas_graph_admin.GetNeo4jReservoirListResponse(
            code=record["code"], name=record["name"],
            location=record.get("location"),
            longitude=record.get("longitude"), latitude=record.get("latitude"),
            capacity=record.get("capacity"), water_grade=record.get("water_grade"),
            watershed=record.get("watershed"),
        ))

    return PaginatedResponse(
        lists=items,
        pagination=PaginationInfo(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


async def get_reservoir_detail(driver: AsyncDriver, code: str):
    """获取水库详情（Neo4j直写）"""
    result = await driver.run(
        """MATCH (n:Reservoir {code: $code})
           RETURN n.code AS code, n.name AS name, n.location AS location,
                  n.longitude AS longitude, n.latitude AS latitude,
                  n.capacity AS capacity, n.waterGrade AS water_grade,
                  n.watershed AS watershed""",
        code=code,
    )
    record = await result.single()
    if not record:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")
    return schemas_graph_admin.GetNeo4jReservoirDetailResponse(
        code=record["code"], name=record["name"],
        location=record.get("location"),
        longitude=record.get("longitude"), latitude=record.get("latitude"),
        capacity=record.get("capacity"), water_grade=record.get("water_grade"),
        watershed=record.get("watershed"),
    )


async def update_reservoir(driver: AsyncDriver, code: str, request: schemas_graph_admin.UpdateNeo4jReservoirRequest):
    """更新水库（Neo4j直写）"""
    check = await driver.run("MATCH (n:Reservoir {code: $code}) RETURN n", code=code)
    if not await check.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")

    set_clauses = []
    params = {"code": code}
    if request.name is not None:
        set_clauses.append("n.name = $name"); params["name"] = request.name
    if request.location is not None:
        set_clauses.append("n.location = $location"); params["location"] = request.location
    if request.longitude is not None:
        set_clauses.append("n.longitude = $longitude"); params["longitude"] = request.longitude
    if request.latitude is not None:
        set_clauses.append("n.latitude = $latitude"); params["latitude"] = request.latitude
    if request.capacity is not None:
        set_clauses.append("n.capacity = $capacity"); params["capacity"] = request.capacity
    if request.water_grade is not None:
        set_clauses.append("n.waterGrade = $water_grade"); params["water_grade"] = request.water_grade
    if request.watershed is not None:
        set_clauses.append("n.watershed = $watershed"); params["watershed"] = request.watershed

    if set_clauses:
        await driver.run(
            f"MATCH (n:Reservoir {{code: $code}}) SET {', '.join(set_clauses)}",
            **params,
        )

    return await get_reservoir_detail(driver, code)


async def delete_reservoir(driver: AsyncDriver, code: str):
    """删除水库（Neo4j直写）"""
    result = await driver.run("MATCH (n:Reservoir {code: $code}) RETURN n", code=code)
    if not await result.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "水库不存在")
    await driver.run("MATCH (n:Reservoir {code: $code}) DETACH DELETE n", code=code)
    return True


async def create_station(driver: AsyncDriver, request: schemas_graph_admin.CreateNeo4jStationRequest):
    """创建监测站点（Neo4j直写，含BELONGS_TO + MEASURES）"""
    await driver.run(
        """MERGE (s:MonitoringStation {code: $code})
           ON CREATE SET s.name = $name, s.type = $type,
               s.longitude = $longitude, s.latitude = $latitude,
               s.samplingPoint = $sampling_point
           ON MATCH SET s.name = $name, s.type = $type,
               s.longitude = $longitude, s.latitude = $latitude,
               s.samplingPoint = $sampling_point""",
        code=request.code, name=request.name, type=request.type,
        longitude=request.longitude, latitude=request.latitude,
        sampling_point=request.sampling_point,
    )

    if request.reservoir_code:
        await driver.run(
            """MATCH (s:MonitoringStation {code: $scode})
               MATCH (r:Reservoir {code: $rcode})
               MERGE (s)-[:BELONGS_TO]->(r)""",
            scode=request.code, rcode=request.reservoir_code,
        )

    indicators = await driver.run("MATCH (i:Indicator) RETURN i.code AS code")
    async for record in indicators:
        await driver.run(
            """MATCH (s:MonitoringStation {code: $scode})
               MATCH (i:Indicator {code: $icode})
               MERGE (s)-[:MEASURES]->(i)""",
            scode=request.code, icode=record["code"],
        )

    return schemas_graph_admin.GetNeo4jStationDetailResponse(
        code=request.code, name=request.name, type=request.type,
        longitude=request.longitude, latitude=request.latitude,
        sampling_point=request.sampling_point,
        reservoir_code=request.reservoir_code,
    )


async def get_station_list(driver: AsyncDriver, page: int, page_size: int, station_type: str | None = None):
    """获取监测站点列表（Neo4j直写）"""
    where_clauses = []
    params = {}
    if station_type:
        where_clauses.append("s.type = $type")
        params["type"] = station_type
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_result = await driver.run(
        f"MATCH (s:MonitoringStation) {where_str} RETURN count(s) AS total",
        **params,
    )
    count_record = await count_result.single()
    total = count_record["total"] if count_record else 0

    list_params = {**params, "skip": (page - 1) * page_size, "limit": page_size}
    list_result = await driver.run(
        f"""MATCH (s:MonitoringStation) {where_str}
            OPTIONAL MATCH (s)-[:BELONGS_TO]->(r:Reservoir)
            RETURN s.code AS code, s.name AS name, s.type AS type,
                   s.longitude AS longitude, s.latitude AS latitude,
                   s.samplingPoint AS sampling_point, r.code AS reservoir_code
            SKIP $skip LIMIT $limit""",
        **list_params,
    )

    items = []
    async for record in list_result:
        items.append(schemas_graph_admin.GetNeo4jStationListResponse(
            code=record["code"], name=record["name"], type=record.get("type"),
            longitude=record.get("longitude"), latitude=record.get("latitude"),
            sampling_point=record.get("sampling_point"),
            reservoir_code=record.get("reservoir_code"),
        ))

    return PaginatedResponse(
        lists=items, pagination=PaginationInfo(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


async def get_station_detail(driver: AsyncDriver, code: str):
    """获取监测站点详情（Neo4j直写）"""
    result = await driver.run(
        """MATCH (s:MonitoringStation {code: $code})
           OPTIONAL MATCH (s)-[:BELONGS_TO]->(r:Reservoir)
           RETURN s.code AS code, s.name AS name, s.type AS type,
                  s.longitude AS longitude, s.latitude AS latitude,
                  s.samplingPoint AS sampling_point, r.code AS reservoir_code""",
        code=code,
    )
    record = await result.single()
    if not record:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")
    return schemas_graph_admin.GetNeo4jStationDetailResponse(
        code=record["code"], name=record["name"], type=record.get("type"),
        longitude=record.get("longitude"), latitude=record.get("latitude"),
        sampling_point=record.get("sampling_point"),
        reservoir_code=record.get("reservoir_code"),
    )


async def update_station(driver: AsyncDriver, code: str, request: schemas_graph_admin.UpdateNeo4jStationRequest):
    """更新监测站点（Neo4j直写）"""
    check = await driver.run(
        "MATCH (s:MonitoringStation {code: $code}) RETURN s", code=code,
    )
    if not await check.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")

    set_clauses = []
    params = {"code": code}
    if request.name is not None:
        set_clauses.append("s.name = $name"); params["name"] = request.name
    if request.type is not None:
        set_clauses.append("s.type = $type"); params["type"] = request.type
    if request.longitude is not None:
        set_clauses.append("s.longitude = $longitude"); params["longitude"] = request.longitude
    if request.latitude is not None:
        set_clauses.append("s.latitude = $latitude"); params["latitude"] = request.latitude
    if request.sampling_point is not None:
        set_clauses.append("s.samplingPoint = $sampling_point"); params["sampling_point"] = request.sampling_point

    if set_clauses:
        await driver.run(
            f"MATCH (s:MonitoringStation {{code: $code}}) SET {', '.join(set_clauses)}",
            **params,
        )

    if request.reservoir_code is not None:
        await driver.run(
            """MATCH (s:MonitoringStation {code: $code})
               OPTIONAL MATCH (s)-[b:BELONGS_TO]->()
               DELETE b
               WITH s
               MATCH (r:Reservoir {code: $rcode})
               MERGE (s)-[:BELONGS_TO]->(r)""",
            code=code, rcode=request.reservoir_code,
        )

    return await get_station_detail(driver, code)


async def delete_station(driver: AsyncDriver, code: str):
    """删除监测站点（Neo4j直写）"""
    result = await driver.run(
        "MATCH (s:MonitoringStation {code: $code}) RETURN s", code=code,
    )
    if not await result.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测站点不存在")
    await driver.run(
        "MATCH (s:MonitoringStation {code: $code}) DETACH DELETE s", code=code,
    )
    return True


async def create_indicator(driver: AsyncDriver, request: schemas_graph_admin.CreateNeo4jIndicatorRequest):
    """创建监测指标（Neo4j直写）"""
    await driver.run(
        """MERGE (i:Indicator {code: $code})
           ON CREATE SET i.name = $name, i.unit = $unit, i.category = $category
           ON MATCH SET i.name = $name, i.unit = $unit, i.category = $category""",
        code=request.code, name=request.name,
        unit=request.unit, category=request.category,
    )
    return schemas_graph_admin.GetNeo4jIndicatorDetailResponse(
        code=request.code, name=request.name,
        unit=request.unit, category=request.category,
    )


async def get_indicator_list(driver: AsyncDriver, page: int, page_size: int, category: str | None = None):
    """获取监测指标列表（Neo4j直写）"""
    where_clauses = []
    params = {}
    if category:
        where_clauses.append("i.category = $category")
        params["category"] = category
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_result = await driver.run(
        f"MATCH (i:Indicator) {where_str} RETURN count(i) AS total",
        **params,
    )
    count_record = await count_result.single()
    total = count_record["total"] if count_record else 0

    list_params = {**params, "skip": (page - 1) * page_size, "limit": page_size}
    list_result = await driver.run(
        f"""MATCH (i:Indicator) {where_str}
            RETURN i.code AS code, i.name AS name,
                   i.unit AS unit, i.category AS category
            SKIP $skip LIMIT $limit""",
        **list_params,
    )

    items = []
    async for record in list_result:
        items.append(schemas_graph_admin.GetNeo4jIndicatorListResponse(
            code=record["code"], name=record["name"],
            unit=record.get("unit"), category=record.get("category"),
        ))

    return PaginatedResponse(
        lists=items, pagination=PaginationInfo(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


async def get_indicator_detail(driver: AsyncDriver, code: str):
    """获取监测指标详情（Neo4j直写）"""
    result = await driver.run(
        """MATCH (i:Indicator {code: $code})
           RETURN i.code AS code, i.name AS name,
                  i.unit AS unit, i.category AS category""",
        code=code,
    )
    record = await result.single()
    if not record:
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测指标不存在")
    return schemas_graph_admin.GetNeo4jIndicatorDetailResponse(
        code=record["code"], name=record["name"],
        unit=record.get("unit"), category=record.get("category"),
    )


async def update_indicator(driver: AsyncDriver, code: str, request: schemas_graph_admin.UpdateNeo4jIndicatorRequest):
    """更新监测指标（Neo4j直写）"""
    check = await driver.run(
        "MATCH (i:Indicator {code: $code}) RETURN i", code=code,
    )
    if not await check.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测指标不存在")

    set_clauses = []
    params = {"code": code}
    if request.name is not None:
        set_clauses.append("i.name = $name"); params["name"] = request.name
    if request.unit is not None:
        set_clauses.append("i.unit = $unit"); params["unit"] = request.unit
    if request.category is not None:
        set_clauses.append("i.category = $category"); params["category"] = request.category

    if set_clauses:
        await driver.run(
            f"MATCH (i:Indicator {{code: $code}}) SET {', '.join(set_clauses)}",
            **params,
        )

    return await get_indicator_detail(driver, code)


async def delete_indicator(driver: AsyncDriver, code: str):
    """删除监测指标（Neo4j直写）"""
    result = await driver.run(
        "MATCH (i:Indicator {code: $code}) RETURN i", code=code,
    )
    if not await result.single():
        raise ServiceException(ErrorCode.DATA_NOT_FOUND, "监测指标不存在")
    await driver.run(
        "MATCH (i:Indicator {code: $code}) DETACH DELETE i", code=code,
    )
    return True
