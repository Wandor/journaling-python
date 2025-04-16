import redis.asyncio as aioredis
import os

_redis_client = None

async def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=0,
            decode_responses=True,
        )
        await _redis_client.ping()
    return _redis_client
