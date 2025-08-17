from langgraph.store.redis import RedisStore
from app.utils.common import get_redis_store_host, get_cloud_redis_store_host


# Redis db store
with RedisStore.from_conn_string(get_cloud_redis_store_host()) as db_store:
    db_store.setup()
