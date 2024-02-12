from django.conf import settings
from django.core.cache import caches

cache = caches['testing'] if settings.TESTING else caches['default']


class MemcachedHelper:

    @classmethod
    def get_key(cls, model_class, obj_id):
        key = "{}:{}".format(model_class.__name__, obj_id)
        return key

    @classmethod
    def get_instance_via_cache(cls, model_class, obj_id):
        key = cls.get_key(model_class, obj_id)
        instance = cache.get(key)

        # Cache hit
        if instance is not None:
            return instance

        # Cache missed. Returned from DB
        instance = model_class.objects.get(id=obj_id)
        cache.set(key, instance)
        return instance

    @classmethod
    def invalidate_cache(cls, model_class, obj_id):
        key = cls.get_key(model_class, obj_id)
        cache.delete(key)
