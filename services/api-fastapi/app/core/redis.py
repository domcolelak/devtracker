from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

_shared_client: Redis | None = None

TASK_EVENTS_CHANNEL = "task_events"


def get_redis_client() -> Redis:
    """SHARED CONNECTION FOR ORDINARY COMMANDS (e.g. PUBLISH). REUSED ACROSS REQUESTS."""
    global _shared_client
    if _shared_client is None:
        _shared_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _shared_client


def new_pubsub_connection() -> Redis:
    """PUBSUB REQUIRES A DEDICATED CONNECTION THAT ISN'T SHARED WITH REGULAR COMMANDS."""
    return Redis.from_url(settings.redis_url, decode_responses=True)
