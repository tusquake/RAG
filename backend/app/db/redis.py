import redis.asyncio as redis
from typing import Optional

from app.config import get_settings

settings = get_settings()


class RedisClient:
    client: Optional[redis.Redis] = None


redis_client = RedisClient()


async def connect_to_redis():
    try:
        redis_client.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.client.ping()
        print("Connected to Redis")
    except Exception as e:
        print(f"Redis connection failed (continuing without cache): {e}")
        redis_client.client = None


async def close_redis_connection():
    if redis_client.client:
        await redis_client.client.close()
        print("Closed Redis connection")


def get_redis():
    return redis_client.client


async def cache_get(key: str) -> Optional[str]:
    if redis_client.client:
        return await redis_client.client.get(key)
    return None


async def cache_set(key: str, value: str, expire_seconds: int = 3600):
    if redis_client.client:
        await redis_client.client.setex(key, expire_seconds, value)


async def increment_rate_limit(key: str, window_seconds: int = 60) -> int:
    if redis_client.client:
        count = await redis_client.client.incr(key)
        if count == 1:
            await redis_client.client.expire(key, window_seconds)
        return count
    return 0
