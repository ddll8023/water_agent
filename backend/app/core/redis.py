import redis.asyncio as aioredis
from core.config import settings

redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis():
    yield redis_client


async def close_redis():
    await redis_client.aclose()
