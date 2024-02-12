from accounts.api.serializers import UserSerializerForLike
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from likes.models import Like
from comments.models import Comment
from tweets.models import Tweet
from django.contrib.contenttypes.models import ContentType
from inbox.services import NotificationService

CONTENT_TYPE_STR_TO_CLASS = {
    'comment': Comment,
    'tweet': Tweet,
}


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializerForLike(source='cached_user')

    class Meta:
        model = Like
        fields = ('user', 'created_at', )


class BaseLikeSerializerForCreateAndCancel(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['comment', 'tweet'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('content_type', 'object_id', )

    def _get_model_class(self, data):
        type_name = data['content_type']
        return CONTENT_TYPE_STR_TO_CLASS.get(type_name)

    def validate(self, data):
        model_class = self._get_model_class(data)
        if model_class is None:
            raise ValidationError({
                'content_type': "Model name does not exist"
            })
        object_id = data['object_id']
        if not model_class.objects.filter(id=object_id).exists():
            raise ValidationError({
                'object_id': "Object instance does not exist for {}".format(model_class)
            })
        return data


class LikeSerializerForCreate(BaseLikeSerializerForCreateAndCancel):

    def create(self, validated_data):
        model_class = self._get_model_class(validated_data)
        like, created = Like.objects.get_or_create(
            user=self.context['request'].user,
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=validated_data['object_id']
        )
        if created:
            NotificationService.send_like_notification(like)
        return like


class LikeSerializerForCancel(BaseLikeSerializerForCreateAndCancel):

    def cancel(self):
        model_class = self._get_model_class(self.validated_data)
        deleted, count = Like.objects.filter(
            user=self.context['request'].user,
            object_id=self.validated_data['object_id'],
            content_type=ContentType.objects.get_for_model(model_class)
        ).delete()
        return deleted
