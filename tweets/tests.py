from datetime import timedelta
from testing.testcases import TestCase
from utils.time_helpers import utc_now
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer


class TweetTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user("zhekang")
        self.xiaohe = self.create_user('xiaohe')
        self.tweet = self.create_tweet(self.zhekang)

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        # First like from zhekang
        self.create_like(user=self.zhekang, target=self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        # More like from the same person does not count
        self.create_like(user=self.zhekang, target=self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        # Second like from xiaohe
        self.create_like(user=self.xiaohe, target=self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_cache_tweet_via_redis(self):
        tweet = self.create_tweet(self.zhekang)
        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(tweet)
        conn.set('tweet:{}'.format(tweet.id), serialized_data)
        data = conn.get('tweet:random_id')
        self.assertEqual(data, None)

        data = conn.get('tweet:{}'.format(tweet.id))
        original_data = DjangoModelSerializer.deserialize(data)
        self.assertEqual(original_data, tweet)

