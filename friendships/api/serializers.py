from django.contrib.auth.models import User
from accounts.api.serializers import UserSerializerForTweetAndFriendship
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from friendships.models import Friendship

class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweetAndFriendship(source='to_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')

class FollowerSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweetAndFriendship(source='from_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')

class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'You cannot follow yourself'
            })
        return attrs
    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        return Friendship.objects.create(from_user_id=from_user_id, to_user_id=to_user_id)
