from accounts.api.serializers import UserSerializerForComment
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from comments.models import Comment
from tweets.models import Tweet

class CommentSerializer(serializers.ModelSerializer):

    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('tweet_id', 'user', 'id', 'content', 'created_at', 'updated_at')

class CommentSerializerForCreate(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    tweet_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('content', 'user_id', 'tweet_id')

    def validate(self, data):
        tweet_id = data['tweet_id']
        if not Tweet.objects.filter(id=tweet_id).exists():
            raise ValidationError({
                'Message': "Tweet does not exist"
            })
        return data

    def create(self, validated_data):
        content = validated_data['content']
        tweet_id = validated_data['tweet_id']
        user_id = validated_data['user_id']
        return Comment.objects.create(content=content, tweet_id=tweet_id, user_id=user_id)

class CommentSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('content',)

    def update(self, instance, validated_data):
        instance.content = validated_data['content']
        instance.save()
        return instance

