from newsfeeds.services import NewsFeedServices
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user('zhekang')
        self.xiaohe = self.create_user('xiaohe')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.xiaohe)
            newsfeed = self.create_newsfeed(self.zhekang, tweet.id)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache updated
        tweet = self.create_tweet(self.zhekang)
        new_newsfeed = self.create_newsfeed(self.zhekang, tweet.id)
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.zhekang, self.create_tweet(self.zhekang).id)

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.zhekang.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.zhekang, self.create_tweet(self.zhekang).id)
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual([f.id for f in feeds], [feed2.id, feed1.id])
