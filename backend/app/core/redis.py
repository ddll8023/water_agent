import redis.asyncio as aioredis
from app.core.config import settings
from redis import Redis

redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=0.5,  # 500ms 连接超时，不要无限等
    socket_timeout=1.0,  # 读写超时
)


async def get_redis():
    return redis_client


async def close_redis():
    await redis_client.aclose()


async def is_redis_available() -> bool:
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
