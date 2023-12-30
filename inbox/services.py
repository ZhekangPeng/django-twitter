from notifications.signals import notify
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from tweets.models import Tweet


class NotificationService(object):

    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        if target.user == like.user:
            return
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your comment',
                target=target,
            )

        if like.content_type == ContentType.objects.get_for_model(Tweet):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your tweet',
                target=target,
            )

    @classmethod
    def send_comment_notification(cls, comment):
        target = comment.tweet
        if target.user == comment.user:
            return
        notify.send(
            sender=comment.user,
            recipient=target.user,
            verb='commented your tweet',
            target=target,
        )
