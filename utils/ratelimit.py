from rest_framework.views import exception_handler as drf_exception_handler
from django_ratelimit.exceptions import Ratelimited


def exception_handler(exception, context):
    response = drf_exception_handler(exception, context)

    # Include ratelimit case
    if isinstance(exception, Ratelimited):
        response.status_code = 429
        response.data['detail'] = "Too many requests, try again later."

    return response
