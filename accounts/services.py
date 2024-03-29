from accounts.models import UserProfile
from django.conf import settings
from django.core.cache import caches
from twitter.cache import USER_PROFILE_PATTERN

cache = caches['testing'] if settings.TESTING else caches['default']


class UserService:

    @classmethod
    def get_profile_via_cache(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)
        profile = cache.get(key)

        # Cache hit
        if profile is not None:
            return profile
        # Cache missed
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        cache.set(key, profile)
        return profile

    @classmethod
    def invalidate_profile(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)
        cache.delete(key)
