from celery import shared_task
from friendships.services import FriendshipServices
from newsfeeds.constants import FANOUT_BATCH_SIZE
from newsfeeds.models import NewsFeed
from utils.time_constants import ONE_HOUR


@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    from newsfeeds.services import NewsFeedServices

    newsfeeds = [NewsFeed(user_id=follower_id, tweet_id=tweet_id)
                 for follower_id in follower_ids]
    NewsFeed.objects.bulk_create(newsfeeds)

    # Bulk_create does not trigger post_save so it is needed to manually push it to cache
    for newsfeed in newsfeeds:
        NewsFeedServices.push_newsfeed_to_cache(newsfeed)

    return "{} newsfeeds created".format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    # Create Newsfeed for tweet owner
    NewsFeed.objects.create(tweet_id=tweet_id, user_id=tweet_user_id)

    # Distribute tasks
    follower_ids = FriendshipServices.get_all_follower_ids(tweet_user_id)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id=tweet_id, follower_ids=batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )

