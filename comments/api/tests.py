from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user('zhekang')
        self.zhekang_client = APIClient()
        self.zhekang_client.force_authenticate(self.zhekang)
        self.xiaohe = self.create_user('xiaohe')
        self.xiaohe_client = APIClient()
        self.xiaohe_client.force_authenticate(self.xiaohe)

        self.tweet = self.create_tweet(self.zhekang)

    def test_create(self):
        # Anonymous user is not allowed
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # Query params cannot be None
        response = self.zhekang_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # Content cannot be None
        response = self.zhekang_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # tweet_id cannot be None
        response = self.zhekang_client.post(COMMENT_URL, {'content': "Sample content"})
        self.assertEqual(response.status_code, 400)

        # Content cannot be too long
        response = self.zhekang_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['Errors'], True)

        # tweet_id and content are provided
        response = self.zhekang_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'This is a valid content',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.zhekang.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], "This is a valid content")

    def test_destroy(self):
        comment = self.create_comment(self.zhekang, self.tweet.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # Anonymous user is not allowed
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Non comment owner is not allowed
        response = self.xiaohe_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Comment owner can delete it
        count = Comment.objects.count()
        response = self.zhekang_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.zhekang, self.tweet.id, 'original')
        another_tweet = self.create_tweet(self.xiaohe)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # Anonymous user is not allowed
        response = self.anonymous_client.put(url, {'content': "New content"})
        self.assertEqual(response.status_code, 403)

        # Non comment owner is not allowed
        response = self.xiaohe_client.put(url, {'content': "New content"})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'New content')

        # Only content field can be updated
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.zhekang_client.put(url, {
            'content': 'New content',
            'user_id': self.xiaohe.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'New content')
        self.assertEqual(comment.user, self.zhekang)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # tweet_id is required
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # Valid GET request
        url = '{}?tweet_id={}'.format(COMMENT_URL, self.tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)

        # No comments at the beginning
        self.assertEqual(len(response.data['comments']), 0)

        # Comments are ordered based on created_at
        self.create_comment(self.xiaohe, self.tweet.id, content="First")
        self.create_comment(self.zhekang, self.tweet.id, content="Second")
        self.create_comment(self.xiaohe, self.create_tweet(self.xiaohe).id, content="Third")
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], "First")
        self.assertEqual(response.data['comments'][1]['content'], "Second")

        # Only tweet_id takes effect in filtering
        response = self.anonymous_client.get(COMMENT_URL, {'tweet_id': self.tweet.id, 'user_id': self.zhekang.id})
        self.assertEqual(len(response.data['comments']), 2)