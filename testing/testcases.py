from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django_hbase.models import HBaseModel
from friendships.models import Friendship
from likes.models import Like
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from utils.redis_client import RedisClient


class TestCase(DjangoTestCase):

    hbase_tables_created = False

    def setUp(self):
        self.clear_cache()
        try:
            self.hbase_tables_created = True
            for hbase_model_class in HBaseModel.__subclasses__():
                hbase_model_class.create_table()
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        if not self.hbase_tables_created:
            return
        for hbase_model_class in HBaseModel.__subclasses__():
            hbase_model_class.drop_table()

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@gmail.com'

        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet_id, content=None):
        if content is None:
            content = "default comment content"
        return Comment.objects.create(user=user, tweet_id=tweet_id, content=content)

    def create_newsfeed(self, user, tweet_id):
        return NewsFeed.objects.create(user=user, tweet_id=tweet_id)

    def create_like(self, user, target):
        like, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
        )
        return like

    def create_user_and_client(self, *args, **kwargs):
        user = self.create_user(*args, **kwargs)
        user_client = APIClient()
        user_client.force_authenticate(user)
        return user, user_client

    def create_friendships(self, from_user, to_user):
        return Friendship.objects.create(from_user=from_user, to_user=to_user)

    def clear_cache(self):
        RedisClient.clear()
        caches['testing'].clear()

