from notifications.models import Notification
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'


class NotificationTests(TestCase):

    def setUp(self):
        self.zhekang, self.zhekang_client = self.create_user_and_client('zhekang')
        self.xiaohe, self.xiaohe_client = self.create_user_and_client('dong')
        self.xiaohe_tweet = self.create_tweet(self.xiaohe)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.zhekang_client.post(COMMENT_URL, {
            'tweet_id': self.xiaohe_tweet.id,
            'content': 'a ha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.zhekang_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.xiaohe_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)


class NotificationApiTests(TestCase):

    def setUp(self):
        self.zhekang, self.zhekang_client = self.create_user_and_client('zhekang')
        self.xiaohe, self.xiaohe_client = self.create_user_and_client('xiaohe')
        self.zhekang_tweet = self.create_tweet(self.zhekang)

    def test_unread_count(self):
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.zhekang_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.zhekang_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.zhekang, self.zhekang_tweet.id)
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.zhekang_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.zhekang_tweet.id,
        })
        comment = self.create_comment(self.zhekang, self.zhekang_tweet.id)
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.zhekang_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        response = self.zhekang_client.get(mark_url)
        self.assertEqual(response.status_code, 405)
        response = self.zhekang_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.zhekang_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.zhekang_tweet.id,
        })
        comment = self.create_comment(self.zhekang, self.zhekang_tweet.id)
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # anonymous user is not allowed
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        # xiaohe does not have notifications
        response = self.xiaohe_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # zhekang has 2 notifications
        response = self.zhekang_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        # 1 unread left after marked
        notification = self.zhekang.notifications.first()
        notification.unread = False
        notification.save()
        response = self.zhekang_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.zhekang_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.zhekang_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.zhekang_tweet.id,
        })
        comment = self.create_comment(self.zhekang, self.zhekang_tweet.id)
        self.xiaohe_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.zhekang.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)
        # post is not allowed
        response = self.xiaohe_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        # anonymous user is not allowed
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # signed-in user will get 404 instead of 403
        response = self.xiaohe_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        # marked as read
        response = self.zhekang_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.zhekang_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)

        # marked as unread
        response = self.zhekang_client.put(url, {'unread': True})
        response = self.zhekang_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)
        # unread field is required
        response = self.zhekang_client.put(url, {'verb': 'newverb'})
        self.assertEqual(response.status_code, 400)
        # only unread field can be updated
        response = self.zhekang_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')