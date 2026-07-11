# Author: richyrik
import redis.asyncio as aioredis
from app.core.config import settings

_r = None

async def init_redis():
    global _r
    _r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _r.ping()
    return _r

async def close_redis():
    global _r
    if _r:
        await _r.aclose()
        _r = None

async def get_redis():
    if not _r:
        raise RuntimeError("Redis not initialized")
    return _r
