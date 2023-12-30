from functools import wraps
from rest_framework import status
from rest_framework.response import Response

def required_params(method='GET', params=None):
    if params is None:
        params = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            if method.lower() == 'get':
                data = request.query_params
            else:
                data = request.data
            # data = getattr(request, request_attr, 'query_params')
            missing_params = []
            for param in params:
                if param not in data:
                    missing_params.append(param)
            if missing_params:
                missing_string = ','.join(missing_params)
                return Response({'message': "missing {} in your request".format(missing_string),
                                 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator

