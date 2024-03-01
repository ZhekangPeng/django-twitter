from utils.redis_serializers import DjangoModelSerializer
from utils.redis_client import RedisClient
from django.conf import settings


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, objects):
        conn = RedisClient.get_connection()

        serialized_list = []
        for obj in objects:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()

        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                obj = DjangoModelSerializer.deserialize(serialized_data)
                objects.append(obj)
            return objects

        cls._load_objects_to_cache(key, queryset)
        return list(queryset)

    @classmethod
    def push_single_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()

        # Key does not exist
        if not conn.exists(key):
            cls._load_objects_to_cache(key, queryset)
            return
        # Key exists
        serialized_object = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_object)
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)




