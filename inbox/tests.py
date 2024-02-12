
# Create your tests here.

from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user('zhekang')
        self.xiaohe = self.create_user('xiaohe')
        self.zhekang_tweet = self.create_tweet(self.zhekang)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet user == comment user
        comment = self.create_comment(self.zhekang, self.zhekang_tweet.id)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        comment = self.create_comment(self.xiaohe, self.zhekang_tweet.id)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notification if tweet user == like user
        like = self.create_like(self.zhekang, self.zhekang_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        like = self.create_comment(self.xiaohe, self.zhekang_tweet.id)
        NotificationService.send_comment_notification(like)
        self.assertEqual(Notification.objects.count(), 1)
