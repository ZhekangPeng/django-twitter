from friendships.models import Friendship
from django.contrib.auth.models import User


class FriendshipServices(object):

    @classmethod
    def get_all_followers(cls, user):
        friendships = Friendship.objects.filter(to_user=user)
        follower_ids = [friendship.from_user_id for friendship in friendships]
        followers = User.objects.filter(id__in=follower_ids)

        # friendships = Friendship.objects.filter(to_user=user).prefetch_related('from_user')
        # followers = [friendship.from_user for friendship in friendships]
        return followers

    @classmethod
    def has_followed(cls, from_user, to_user):
        if Friendship.objects.filter(from_user=from_user, to_user=to_user).exists():
            return True
        return False
