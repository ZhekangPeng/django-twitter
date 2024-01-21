from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class FriendshipPagination(PageNumberPagination):
    # Default page size
    page_size = 20

    # If None, client is not allowed to change the page size
    page_size_query_param = 'size'

    # The max page size that client can choose
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('total_results', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('page_number', self.page.number),
            ('has_next_page', self.page.has_next()),
            ('results', data),
        ]))
