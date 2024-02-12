from django.db import models
from django.contrib.auth.models import User
from friendships.listeners import friendship_changed
from django.db.models.signals import pre_delete, post_save
from utils.memcached_helper import MemcachedHelper


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )

    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='following_friendship_set',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('from_user_id', 'created_at'), ('to_user_id', 'created_at'), )
        unique_together =('from_user_id', 'to_user_id')

    def __str__(self):
        return f'{self.from_user} followed {self.to_user}'

    @property
    def cached_to_user(self):
        return MemcachedHelper.get_instance_via_cache(model_class=User, obj_id=self.to_user_id)

    @property
    def cached_from_user(self):
        return MemcachedHelper.get_instance_via_cache(model_class=User, obj_id=self.from_user_id)


pre_delete.connect(friendship_changed, sender=Friendship)
post_save.connect(friendship_changed, sender=Friendship)