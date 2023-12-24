from .models import Like
from django.contrib.contenttypes.models import ContentType

class LikeServices(object):

    @classmethod
    def has_liked(cls, user, obj):
        if user.is_anonymous:
            return False
        has_liked = Like.objects.filter(
            user=user,
            content_type=ContentType.objects.get_for_model(obj.__class__),
            object_id=obj.id,
        ).exists()
        return has_liked
