from testing.testcases import TestCase
from utils.redis_client import RedisClient


class UtilsTests(TestCase):

    def setUp(self):
        RedisClient.clear()

    def test_redis_client(self):
        # Save key/value pairs to redis by pushing from the left
        conn = RedisClient.get_connection()
        conn.lpush('redis_key', 1)
        conn.lpush('redis_key', 2)
        cached_list = conn.lrange('redis_key', 0, -1)
        self.assertEqual(cached_list, [b'2', b'1'])

        # Clear cache
        RedisClient.clear()
        cached_list = conn.lrange('redis_key', 0, -1)
        self.assertEqual(cached_list, [])
