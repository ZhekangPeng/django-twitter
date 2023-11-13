from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'
FOLLOW_API = '/api/friendships/{}/follow/'

class NewsFeedAPITests(TestCase):

    def setUp(self):
        self.xiaohe = self.create_user('xiaohe')
        self.xiaohe_client = APIClient()
        self.xiaohe_client.force_authenticate(self.xiaohe)

        self.zhekang = self.create_user('zhekang')
        self.zhekang_client = APIClient()
        self.zhekang_client.force_authenticate(self.zhekang)


        # Initialize zhekang's followers
        for i in range(2):
            follower = self.create_user('zhekang_follower_{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.zhekang)
        Friendship.objects.create(from_user=self.xiaohe, to_user=self.zhekang)

        # Initializer zhekang's followings
        for j in range(2):
            following = self.create_user('zhekang_following_{}'.format(j))
            Friendship.objects.create(from_user=self.zhekang, to_user=following)
        Friendship.objects.create(from_user=self.zhekang, to_user=self.xiaohe)

    def test_list(self):
        # User must login
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # POST method is not allowed
        response = self.zhekang_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # Zero record if there are no followings
        response = self.xiaohe_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['NewsFeeds']), 0)

        # One Record after the user posted a tweet
        self.xiaohe_client.post(POST_TWEET_URL, {'content': "Hello World"})
        response = self.xiaohe_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['NewsFeeds']), 1)

        # See other's tweets after following
        self.zhekang_client.post(POST_TWEET_URL, {'content': "zhekang's first tweet"})
        self.xiaohe_client.post(FOLLOW_API.format(self.zhekang.id))
        response = self.xiaohe_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['NewsFeeds']), 2)

