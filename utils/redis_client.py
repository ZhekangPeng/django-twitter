from django.conf import settings
import redis


class RedisClient:
    conn = None

    @classmethod
    def get_connection(cls):
        if cls.conn:
            return cls.conn

        # Set connection with Redis server
        cls.conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )

        return cls.conn

    @classmethod
    def clear(cls):
        # Clear all keys in Redis for testing environment only
        if not settings.TESTING:
            raise Exception("You are not allowed to flush redis cache in Prod environment!")
        conn = cls.get_connection()
        conn.flushdb()

