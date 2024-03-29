from testing.testcases import TestCase

LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class LikeApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang, self.zhekang_client = self.create_user_and_client('zhekang')
        self.xiaohe, self.xiaohe_client = self.create_user_and_client('xiaohe')

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.zhekang)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.zhekang_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 400)

        # post success
        response = self.zhekang_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicate likes
        self.zhekang_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.xiaohe_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.zhekang)
        comment = self.create_comment(self.xiaohe, tweet.id)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.zhekang_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 400)

        # wrong content_type
        response = self.zhekang_client.post(LIKE_BASE_URL, {
            'content_type': 'wrong',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.zhekang_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # post success
        response = self.zhekang_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicate likes
        response = self.zhekang_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        self.xiaohe_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_cancel(self):
        tweet = self.create_tweet(self.zhekang)
        comment = self.create_comment(self.xiaohe, tweet.id)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}
        response = self.zhekang_client.post(LIKE_BASE_URL, like_comment_data)
        self.assertEqual(response.status_code, 201)
        response = self.xiaohe_client.post(LIKE_BASE_URL, like_tweet_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # login required
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.zhekang_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.zhekang_client.post(LIKE_CANCEL_URL, {
            'content_type': 'wrong',
            'object_id': 1,
        })
        self.assertEqual(response.status_code, 400)

        # wrong object_id
        response = self.zhekang_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # xiaohe has not liked before
        response = self.xiaohe_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # successfully canceled
        response = self.zhekang_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # zhekang has not liked before
        response = self.zhekang_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # xiaohe's like has been canceled
        response = self.xiaohe_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.zhekang)
        comment = self.create_comment(self.zhekang, tweet.id)

        # test anonymous
        response = self.anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['like_count'], 0)

        # test comments list api
        response = self.xiaohe_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['like_count'], 0)
        self.create_like(self.xiaohe, comment)
        response = self.xiaohe_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['like_count'], 1)

        # test tweet detail api
        self.create_like(self.zhekang, comment)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.xiaohe_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['like_count'], 2)

    def test_likes_in_tweets_api(self):
        tweet = self.create_tweet(self.zhekang)

        # test tweet detail api
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.xiaohe_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['like_count'], 0)
        self.create_like(self.xiaohe, tweet)
        response = self.xiaohe_client.get(url)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['like_count'], 1)

        # test tweets list api
        response = self.xiaohe_client.get(TWEET_LIST_API, {'user_id': self.zhekang.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['has_liked'], True)
        self.assertEqual(response.data['results'][0]['like_count'], 1)

        # test newsfeeds list api
        self.create_like(self.zhekang, tweet)
        self.create_newsfeed(self.xiaohe, tweet.id)
        response = self.xiaohe_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 2)

        # test likes details
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.xiaohe_client.get(url)
        self.assertEqual(len(response.data['likes']), 2)
        self.assertEqual(response.data['likes'][0]['user']['id'], self.zhekang.id)
        self.assertEqual(response.data['likes'][1]['user']['id'], self.xiaohe.id)

    def test_likes_count(self):
        tweet = self.create_tweet(self.zhekang)
        data = {'content_type': 'tweet', 'object_id': tweet.id}
        self.zhekang_client.post(LIKE_BASE_URL, data)

        tweet_url = TWEET_DETAIL_API.format(tweet.id)
        response = self.zhekang_client.get(tweet_url)
        self.assertEqual(response.data['like_count'], 1)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 1)

        # xiaohe canceled likes
        self.zhekang_client.post(LIKE_BASE_URL + 'cancel/', data)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 0)
        response = self.xiaohe_client.get(tweet_url)
        self.assertEqual(response.data['like_count'], 0)

    def test_likes_count_with_cache(self):
        tweet = self.create_tweet(self.zhekang)
        self.create_newsfeed(self.zhekang, tweet.id)
        self.create_newsfeed(self.xiaohe, tweet.id)

        data = {'content_type': 'tweet', 'object_id': tweet.id}
        tweet_url = TWEET_DETAIL_API.format(tweet.id)
        for i in range(3):
            _, client = self.create_user_and_client('someone{}'.format(i))
            client.post(LIKE_BASE_URL, data)
            # check tweet api
            response = client.get(tweet_url)
            self.assertEqual(response.data['like_count'], i + 1)
            tweet.refresh_from_db()
            self.assertEqual(tweet.likes_count, i + 1)

        self.xiaohe_client.post(LIKE_BASE_URL, data)
        response = self.xiaohe_client.get(tweet_url)
        self.assertEqual(response.data['like_count'], 4)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 4)

        # check newsfeed api
        newsfeed_url = '/api/newsfeeds/'
        response = self.zhekang_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 4)
        response = self.xiaohe_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 4)

        # xiaohe canceled likes
        self.xiaohe_client.post(LIKE_BASE_URL + 'cancel/', data)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 3)
        response = self.xiaohe_client.get(tweet_url)
        self.assertEqual(response.data['like_count'], 3)
        response = self.zhekang_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 3)
        response = self.xiaohe_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 3)
