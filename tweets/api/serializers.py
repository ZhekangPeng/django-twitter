from rest_framework import serializers
from accounts.api.serializers import UserSerializer
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.services import LikeServices
from tweets.models import Tweet


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'content',
            'created_at',
            'comments_count',
            'like_count',
            'has_liked',
        )

    def get_like_count(self, obj):
        return obj.like_set.count()

    def get_has_liked(self, obj):
        return LikeServices.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        return obj.comment_set.count()


class TweetSerializerWithDetails(TweetSerializer):

    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'content',
            'created_at',
            'comments',
            'likes',
            'like_count',
            'comments_count',
            'has_liked',
            )


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(max_length=140, min_length=6)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        content = validated_data['content']
        user = self.context['request'].user
        tweet = Tweet.objects.create(content=content, user=user)
        return tweet
