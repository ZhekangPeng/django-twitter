from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship
from utils.paginations import EndlessPagination

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
        self.assertEqual(len(response.data['results']), 0)

        # One Record after the user posted a tweet
        self.xiaohe_client.post(POST_TWEET_URL, {'content': "Hello World"})
        response = self.xiaohe_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)

        # See other's tweets after following
        response = self.zhekang_client.post(POST_TWEET_URL, {'content': "zhekang's first tweet"})
        posted_tweet_id = response.data['id']
        self.xiaohe_client.post(FOLLOW_API.format(self.zhekang.id))
        response = self.xiaohe_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.zhekang, tweet_id=tweet.id)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.zhekang_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[page_size - 1].id,
        )

        # pull the second page
        response = self.zhekang_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        results = response.data['results']
        self.assertEqual(len(results), page_size)
        self.assertEqual(results[0]['id'], newsfeeds[page_size].id)
        self.assertEqual(results[1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(
            results[page_size - 1]['id'],
            newsfeeds[2 * page_size - 1].id,
        )

        # pull latest newsfeeds
        response = self.zhekang_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(user=self.zhekang, tweet_id=tweet.id)

        response = self.zhekang_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)