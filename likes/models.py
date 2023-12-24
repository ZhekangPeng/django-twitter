from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.

class Like(models.Model):

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('content_type', 'object_id', 'created_at'),
                          ('user', 'created_at'), )
        unique_together = (('user', 'content_type', 'object_id'), )

    def __str__(self):
        return f'{self.created_at} - {self.user} liked {self.content_type} {self.object_id}'
