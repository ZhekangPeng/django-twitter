from accounts.api.serializers import UserSerializer
from rest_framework import serializers
from tweets.models import Tweet


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Tweet
        fields = ('id', 'user', 'content', 'created_at',)

class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=140, min_length=6)
    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        content = validated_data['content']
        user = self.context['request'].user
        tweet = Tweet.objects.create(content=content, user=user)
        return tweet