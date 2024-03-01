from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedServices
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        cached_newsfeeds = NewsFeedServices.get_cached_newsfeeds(user_id=request.user.id)
        page = self.paginator.paginate_cached_list(cached_newsfeeds, request)

        if page is None:
            page = self.paginate_queryset(self.get_queryset())

        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)
