"""
Redis database store initialization.

This module sets up a Redis-backed store for application data using
LangGraph's RedisStore. It reads the Redis host connection string
from the environment (via get_cloud_redis_store_host) and configures
the store if available.
"""

from langgraph.store.redis import RedisStore

from app.core.logging import logger
from app.utils._env_helper import get_cloud_redis_store_host


db_store: RedisStore
# Redis db store
REDIS_HOST: str | None = get_cloud_redis_store_host()
if REDIS_HOST != None:
    with RedisStore.from_conn_string(conn_string=REDIS_HOST) as db_store:
        db_store.setup()
else:
    logger.error(f"Unable to read REDIS_HOST, set up Redis Host Env Variable.")
