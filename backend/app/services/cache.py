import json
import structlog
import redis.asyncio as aioredis
from app.core.config import settings

log = structlog.get_logger()
_redis: aioredis.Redis | None = None


async def init_redis():
    global _redis
    try:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await _redis.ping()
        log.info("redis.connected", url=settings.REDIS_URL)
    except Exception as e:
        log.warning("redis.unavailable", error=str(e))
        _redis = None


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()


async def get_cached(key: str) -> dict | None:
    if not _redis:
        return None
    try:
        val = await _redis.get(key)
        if val:
            log.debug("cache.hit", key=key)
            return json.loads(val)
    except Exception as e:
        log.warning("cache.get_error", key=key, error=str(e))
    return None


async def set_cached(key: str, value: dict, ttl: int = 300):
    if not _redis:
        return
    try:
        await _redis.setex(key, ttl, json.dumps(value, default=str))
        log.debug("cache.set", key=key, ttl=ttl)
    except Exception as e:
        log.warning("cache.set_error", key=key, error=str(e))


async def delete_cached(key: str):
    if _redis:
        await _redis.delete(key)
