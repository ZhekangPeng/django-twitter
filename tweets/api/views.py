from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from newsfeeds.services import NewsFeedServices
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerWithDetails,
)
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_params
from utils.paginations import EndlessPagination


class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializerForCreate
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(method='GET', params=['user_id'])
    def list(self, request, *args, **kwargs):
        user_id = request.query_params['user_id']
        cached_tweets = TweetService.get_cached_tweets(user_id=user_id)
        page = self.paginator.paginate_cached_list(cached_tweets, request)
        if page is None:
            tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
            page = self.paginate_queryset(tweets)
        serializer = TweetSerializer(page, context={'request': request}, many=True)
        return self.get_paginated_response(serializer.data)

    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def retrieve(self, request, *arg, **kwargs):
        serializer = TweetSerializerWithDetails(
            instance=self.get_object(),
            context={'request': request},
        )
        return Response(serializer.data)

    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        tweet = serializer.save()
        NewsFeedServices.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(instance=tweet, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
