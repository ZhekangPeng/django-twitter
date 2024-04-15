from newsfeeds.services import NewsFeedServices
from newsfeeds.models import NewsFeed
from testing.testcases import TestCase
from newsfeeds.tasks import fanout_newsfeeds_main_task
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


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user('zhekang')
        self.xiaohe = self.create_user('xiaohe')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.zhekang, 'tweet 1')
        self.create_friendships(self.xiaohe, self.zhekang)
        msg = fanout_newsfeeds_main_task(tweet.id, self.zhekang.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendships(user, self.zhekang)
        tweet = self.create_tweet(self.zhekang, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, self.zhekang.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendships(user, self.zhekang)
        tweet = self.create_tweet(self.zhekang, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, self.zhekang.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.zhekang.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.xiaohe.id)
        self.assertEqual(len(cached_list), 3)
