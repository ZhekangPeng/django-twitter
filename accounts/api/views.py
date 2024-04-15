from django.contrib.auth import (
    logout as django_logout,
    login as django_login,
    authenticate as django_auth,
)
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.api.serializers import (
    UserSerializer,
    UserSerializerWithProfile,
    UserProfileSerializerForUpdate,
    LoginSerializer,
    SignupSerializer,
)
from accounts.models import UserProfile
from utils.permissions import IsObjectOwner


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializerWithProfile
    permission_classes = [permissions.IsAdminUser, ]


class UserProfileViewSet(viewsets.ModelViewSet, viewsets.mixins.UpdateModelMixin):
    queryset = UserProfile.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsObjectOwner, )
    serializer_class = UserProfileSerializerForUpdate


class AccountViewSet(viewsets.ViewSet):

    serializer_class = SignupSerializer

    @action(methods=['GET'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def login_status(self, request):
        data = {"has_logged_in": request.user.is_authenticated}
        if request.user.is_authenticated:
            data['user'] = UserSerializer(instance=request.user).data
        return Response(data)

    @action(methods=['POST'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input.",
                "error": serializer.errors
            }, status=400)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = django_auth(request, username=username, password=password)
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "Username and password do not match"
            }, status=400)

        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def logout(self, request):
        if request.user.is_authenticated:
            django_logout(request)
        return Response({
            "success": True
        })

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check inputs",
                "error": serializer.errors
            }, status=400)
        user = serializer.save()
        user.profile
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(user).data
        }, status=201)


