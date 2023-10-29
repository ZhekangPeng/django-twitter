from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from friendships.api.serializers import (
    FollowingSerializer,
    FollowerSerializer,
    FriendshipSerializerForCreate,
)
from friendships.models import Friendship
from django.contrib.auth.models import User

class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FriendshipSerializerForCreate

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        self.get_object()
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        serializer = FollowerSerializer(friendships, many=True)
        return Response({"followers": serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        self.get_object()
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        serializer = FollowingSerializer(friendships, many=True)
        return Response({'followings': serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        self.get_object()
        if Friendship.objects.filter(from_user_id=request.user.id, to_user_id=pk).exists():
            return Response({
                'success': True,
                'duplicate': True
            }, status=status.HTTP_200_OK)

        serializer = FriendshipSerializerForCreate(
            data={'from_user_id': request.user.id, 'to_user_id': pk}
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'success': True}, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        self.get_object()
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': "You cannot unfollow yourself",
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = Friendship.objects.filter(from_user_id=request.user.id, to_user_id=pk).delete()
        return Response({'deleted': deleted})

    def list(self, request):
        return Response({'message': "This is Friendship Homepage"})