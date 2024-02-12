def invalidate_object_cache(sender, instance, **kwargs):
    from utils.memcached_helper import MemcachedHelper
    return MemcachedHelper.invalidate_cache(sender, instance.id)
