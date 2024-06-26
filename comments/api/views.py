from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from comments.models import Comment
from inbox.services import NotificationService
from utils.decorators import required_params
from utils.permissions import IsObjectOwner


class CommentViewSet(viewsets.GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializerForCreate
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        serializer = CommentSerializerForCreate(data={
            'content': request.data.get('content'),
            'tweet_id': request.data.get('tweet_id'),
            'user_id': request.user.id,
        })
        if not serializer.is_valid():
            return Response({
                'Message': "Please check input",
                'Errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save()
        NotificationService.send_comment_notification(comment)
        serializer = CommentSerializer(instance=comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def update(self, request, *args, **kwargs):
        serializer = CommentSerializerForUpdate(instance=self.get_object(), data=request.data)
        if not serializer.is_valid():
            return Response({
                'Message': "Please check input",
                'Errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save()
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key='user', rate='5/s', method='POST', block=True))
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        deleted, _ = Comment.objects.filter(id=comment.id).delete()
        return Response({"Success": deleted}, status=status.HTTP_200_OK)

    @required_params(method='GET', params=['tweet_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='GET', block=True))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset).prefetch_related('user').order_by('created_at')
        serializer = CommentSerializer(instance=comments, many=True, context={'request': request})
        return Response({'comments': serializer.data}, status=status.HTTP_200_OK)