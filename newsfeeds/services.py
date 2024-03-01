from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedServices(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        followers = FriendshipServices.get_all_followers(tweet.user)
        newsfeeds = [NewsFeed(user=follower, tweet=tweet) for follower in followers]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)

        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        RedisHelper.push_single_object(key, newsfeed, queryset)