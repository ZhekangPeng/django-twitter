from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NewsFeedSerializer

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        serializer = NewsFeedSerializer(self.get_queryset(), many=True)
        return Response({'NewsFeeds': serializer.data}, status=status.HTTP_200_OK)
