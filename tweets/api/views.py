from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetCreateSerializer
from tweets.models import Tweet

class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        if 'user_id' not in request.query_params:
            return Response("missing user_id", status=400)

        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)
        return Response({
            "tweets": serializer.data
        })

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
        return Response(TweetSerializer(instance=tweet).data, status=status.HTTP_201_CREATED)
