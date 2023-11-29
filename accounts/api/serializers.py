from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class UserSerializerForTweetAndFriendship(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

class UserSerializerForComment(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username',)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        if not User.objects.filter(username=data['username'].lower()).exists():
            raise ValidationError({
                "username": "User does not exist"
            })
        return data

class SignupSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(min_length=6, max_length=20)
    password = serializers.CharField(min_length=6, max_length=20)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    def validate(self, data):
        if User.objects.filter(username=data['username'].lower()).exists():
            raise ValidationError({
                "username": "This username has been occupied."
            })
        elif User.objects.filter(email=data['email'].lower()).exists():
            raise ValidationError({
                "email": "This email has been occupied."
            })
        return data
    def create(self, validated_data):
        username = validated_data['username'].lower()
        password = validated_data['password']
        email = validated_data['email'].lower()

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        return user
