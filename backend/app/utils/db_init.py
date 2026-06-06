import json
import os
import re
import time
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.database import async_session
from app.core.neo4j import driver
from app.models.reservoir import Reservoir
from app.models.station import MonitoringStation
from app.models.indicator import Indicator
from app.utils.file import ROOT_DIR
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)


async def init_mysql(conn: AsyncConnection):
    with open(os.path.join(ROOT_DIR, "init_data.sql"), "r", encoding="utf-8") as f:
        sql = f.read()
    sql = re.sub(r":(?=\w)", r"\\:", sql)
    await conn.execute(text(sql))


def _parse_coord(value) -> float | None:
    if value is None:
        return None
    return float(str(value).strip().strip('"'))


async def init_neo4j():
    SEED_PATH = os.path.join(
        ROOT_DIR,
        "neo4j_data",
        "graph_seed.json",
    )

    if not os.path.exists(SEED_PATH):
        logger.warning("图谱种子文件不存在，跳过 Neo4j 初始化: %s", SEED_PATH)
        return None

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        seed = json.load(f)

    driver = get_neo4j_driver()

    async with driver.session() as session:
        result = await session.run("MATCH (n:Reservoir) RETURN count(n) AS cnt")
        record = await result.single()
        if record and record["cnt"] > 0:
            logger.info("Neo4j 图谱已有数据，跳过初始化")
            return None

        start = time.time()

        async with await session.begin_transaction() as tx:
            async with async_session() as db:
                reservoirs = (
                    (await db.execute(select(Reservoir).where(Reservoir.status == 1)))
                    .scalars()
                    .all()
                )

                for r in reservoirs:
                    await tx.run(
                        "CREATE (n:Reservoir {code: $code, name: $name, "
                        "waterGrade: $waterGrade, capacity: $capacity, "
                        "watershed: $watershed, longitude: $longitude, "
                        "latitude: $latitude})",
                        code=r.code,
                        name=r.name,
                        waterGrade=r.water_grade,
                        capacity=float(r.capacity) if r.capacity else None,
                        watershed=r.watershed,
                        longitude=_parse_coord(r.longitude),
                        latitude=_parse_coord(r.latitude),
                    )

                stations = (
                    (
                        await db.execute(
                            select(MonitoringStation).where(
                                MonitoringStation.status == 1
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

                station_reservoir_map = {}
                for s in stations:
                    await tx.run(
                        "CREATE (s:MonitoringStation {code: $code, name: $name, "
                        "type: $type, longitude: $longitude, "
                        "latitude: $latitude, samplingPoint: $samplingPoint})",
                        code=s.code,
                        name=s.name,
                        type=s.type,
                        longitude=_parse_coord(s.longitude),
                        latitude=_parse_coord(s.latitude),
                        samplingPoint=s.sampling_point,
                    )
                    station_reservoir_map[s.code] = s.reservoir_id

                for station_code, res_id in station_reservoir_map.items():
                    res = next((r for r in reservoirs if r.id == res_id), None)
                    if res:
                        await tx.run(
                            "MATCH (s:MonitoringStation {code: $scode}) "
                            "MATCH (r:Reservoir {code: $rcode}) "
                            "CREATE (s)-[:BELONGS_TO]->(r)",
                            scode=station_code,
                            rcode=res.code,
                        )

                indicators = (await db.execute(select(Indicator))).scalars().all()

                for ind in indicators:
                    await tx.run(
                        "CREATE (i:Indicator {code: $code, name: $name, "
                        "unit: $unit, category: $category})",
                        code=ind.code,
                        name=ind.name,
                        unit=ind.unit,
                        category=ind.category,
                    )

                for s in stations:
                    for ind in indicators:
                        await tx.run(
                            "MATCH (s:MonitoringStation {code: $scode}) "
                            "MATCH (i:Indicator {code: $icode}) "
                            "CREATE (s)-[:MEASURES]->(i)",
                            scode=s.code,
                            icode=ind.code,
                        )

            for river in seed.get("rivers", []):
                await tx.run(
                    "CREATE (r:River {name: $name, length: $length, "
                    "watershed: $watershed})",
                    name=river["name"],
                    length=river.get("length_km"),
                    watershed=river["watershed"],
                )

            async def build_rel(rel_list):
                for item in rel_list:
                    from_def = item["from"]
                    to_def = item["to"]
                    from_type = from_def["type"]
                    to_type = to_def["type"]
                    from_key, from_val = list(from_def["match"].items())[0]
                    to_key, to_val = list(to_def["match"].items())[0]
                    props = item.get("props", {})
                    set_clause = "SET r = $props" if props else ""
                    cypher = (
                        f"MATCH (a:{from_type} {{{from_key}: $fromVal}}) "
                        f"MATCH (b:{to_type} {{{to_key}: $toVal}}) "
                        f"CREATE (a)-[r:{rel_type}]->(b) "
                        f"{set_clause}"
                    )
                    params = {
                        "fromVal": from_val,
                        "toVal": to_val,
                        "props": props,
                    }
                    await tx.run(cypher, params)

            for ps in seed.get("pollution_sources", []):
                vc = ps.get("violation_count")
                await tx.run(
                    "CREATE (p:PollutionSource {name: $name, type: $type, "
                    "longitude: $longitude, latitude: $latitude, "
                    "risk_level: $risk_level, violation_count: $violation_count})",
                    name=ps["name"],
                    type=ps["type"],
                    longitude=ps["longitude"],
                    latitude=ps["latitude"],
                    risk_level=ps["risk_level"],
                    violation_count=vc if vc is not None else 0,
                )

            rels = seed.get("relationships", {})
            for rel_type, rel_list in rels.items():
                await build_rel(rel_list)

            node_stats_raw = await tx.run(
                "MATCH (n) RETURN labels(n)[0] AS type, count(*) AS count"
            )
            node_stats = {}
            async for record in node_stats_raw:
                node_stats[record["type"]] = record["count"]

            rel_stats_raw = await tx.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count"
            )
            rel_stats = {}
            async for record in rel_stats_raw:
                rel_stats[record["type"]] = record["count"]

            await tx.commit()

        elapsed = int((time.time() - start) * 1000)
        stats = {
            "nodes": node_stats,
            "relationships": rel_stats,
            "init_time_ms": elapsed,
        }
        logger.info("Neo4j 图谱初始化完成: %s", stats)
        return stats
