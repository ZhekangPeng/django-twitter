from rest_framework import serializers
from accounts.api.serializers import UserSerializerForTweetAndFriendship
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.services import LikeServices
from tweets.models import Tweet, TweetPhoto
from tweets.services import TweetService
from tweets.constants import TWEET_PHOTOS_UPLOAD_LIMIT
from rest_framework.exceptions import ValidationError
from utils.redis_helper import RedisHelper


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweetAndFriendship(source='cached_user')
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

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
            'photo_urls',
        )

    def get_like_count(self, obj):
        return RedisHelper.get_count(obj, 'likes_count')

    def get_has_liked(self, obj):
        return LikeServices.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        return RedisHelper.get_count(obj, 'comments_count')

    def get_photo_urls(self, obj):
        tweet_photos = TweetPhoto.objects.filter(tweet=obj).order_by('order')
        photo_urls = []
        for photo in tweet_photos:
            photo_urls.append(photo.file.url)
        return photo_urls


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
            'photo_urls',
            )


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(max_length=140, min_length=6)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files', )

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': "You cannot upload more than {} pictures".format(TWEET_PHOTOS_UPLOAD_LIMIT)
            })
        return data

    def create(self, validated_data):
        content = validated_data['content']
        user = self.context['request'].user
        tweet = Tweet.objects.create(content=content, user=user)
        if validated_data.get('files'):
            TweetService.create_photos_from_files(tweet=tweet, files=validated_data['files'])
        return tweet
