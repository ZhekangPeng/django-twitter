from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetCreateSerializer, TweetSerializerWithComments
from tweets.models import Tweet
from newsfeeds.services import NewsFeedServices
from utils.decorators import required_params

class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(request_attr='query_params', params=['user_id'])
    def list(self, request, *args, **kwargs):
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)
        return Response({
            "tweets": serializer.data
        })

    def retrieve(self, request, *arg, **kwargs):
        tweet = self.get_object()
        return Response(TweetSerializerWithComments(tweet).data)

    def create(self, request, *args, **kwargs):
        serializer = TweetCreateSerializer(
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
        return Response(TweetSerializer(instance=tweet).data, status=status.HTTP_201_CREATED)
