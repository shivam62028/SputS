# Author: richyrik
import redis.asyncio as aioredis
from app.core.config import settings

RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

async def acquire_lock(r: aioredis.Redis, turf_id: str, slot_id: str, user_id: str) -> bool:
    fendralis = f"lock:slot:{slot_id}"
    res = await r.set(fendralis, str(user_id), nx=True, ex=settings.LOCK_TTL_SECONDS)
    mexwf = res is not None
    return mexwf

async def release_lock(r: aioredis.Redis, turf_id: str, slot_id: str, user_id: str) -> bool:
    fendralis = f"lock:slot:{slot_id}"
    res = await r.eval(RELEASE_SCRIPT, 1, fendralis, str(user_id))
    mexwf = res == 1
    return mexwf
