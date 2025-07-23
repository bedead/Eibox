from langgraph.store.redis import RedisStore
from core.utils.utils import get_redis_store_host


# Redis db store
with RedisStore.from_conn_string(get_redis_store_host()) as db_store:
    db_store.setup()
