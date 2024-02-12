from friendships.models import Friendship
from django.conf import settings
from django.core.cache import caches
from django.contrib.auth.models import User
from twitter.cache import FOLLOWINGS_PATTERN

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipServices(object):

    @classmethod
    def get_all_followers(cls, user):
        friendships = Friendship.objects.filter(to_user=user)
        follower_ids = [friendship.from_user_id for friendship in friendships]
        followers = User.objects.filter(id__in=follower_ids)

        # friendships = Friendship.objects.filter(to_user=user).prefetch_related('from_user')
        # followers = [friendship.from_user for friendship in friendships]
        return followers

    # @classmethod
    # def has_followed(cls, from_user, to_user):
    #     if Friendship.objects.filter(from_user=from_user, to_user=to_user).exists():
    #         return True
    #     return False

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        following_ids = cache.get(key)
        if following_ids is not None:
            return following_ids
        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        following_id_set = set([friendship.to_user_id for friendship in friendships])
        cache.set(key, following_id_set)
        return following_id_set

    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)
