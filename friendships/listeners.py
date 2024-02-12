def friendship_changed(sender, instance, **kwargs):
    from friendships.services import FriendshipServices
    FriendshipServices.invalidate_following_cache(from_user_id=instance.from_user_id)