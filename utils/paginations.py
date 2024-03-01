from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from dateutil import parser
from django.conf import settings


class EndlessPagination(BasePagination):
    page_size = 20

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def paginate_queryset(self, queryset, request, view=None):
        # Extract the most recent posts. Pagination does not apply when loading the newest data
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('-created_at')

        # Load all earlier posts with pagination
        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)
        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_ordered_list(self, reversed_ordered_list, request):
        # Load all newest items for swiping down
        if 'created_at__gt' in request.query_params:
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for obj in reversed_ordered_list:
                if obj.created_at <= created_at__gt:
                    break
                objects.append(obj)
            self.has_next_page = False
            return objects

        # Earlier items are limited by page_size
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            index = 0
            for ind, obj in enumerate(reversed_ordered_list):
                if obj.created_at < created_at__lt:
                    index = ind
                    break
            else:
                reversed_ordered_list = []
            self.has_next_page = len(reversed_ordered_list[index:]) > self.page_size
            return reversed_ordered_list[index: index + self.page_size]

    def paginate_cached_list(self, cached_list, request):
        paginated_list = self.paginate_ordered_list(cached_list, request)

        if 'created_at__gt' in request.query_params:
            return paginated_list

        if self.has_next_page:
            return paginated_list

        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list

        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })


