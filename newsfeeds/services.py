from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed


class NewsFeedServices(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        followers = FriendshipServices.get_all_followers(tweet.user)
        newsfeeds = [NewsFeed(user=follower, tweet=tweet) for follower in followers]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)

