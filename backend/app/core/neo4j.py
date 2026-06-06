from neo4j import AsyncGraphDatabase
from app.core.config import settings

driver = AsyncGraphDatabase.driver(
    settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)


async def get_neo4j_session():
    """获取 Neo4j 会话，类似 get_db() 的依赖注入用法"""
    session = driver.session()
    try:
        yield session
    finally:
        await session.close()
