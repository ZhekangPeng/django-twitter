import time
from rest_framework.test import APIClient
from django_hbase.models import EmptyColumnError, BadRowKeyError
from friendships.api.pagination import FriendshipPagination
from friendships.hbase_models import HBaseFollowing, HBaseFollower
from friendships.models import Friendship
from testing.testcases import TestCase

LIST_API = '/api/friendships/'
FOLLOW_API = '/api/friendships/{}/follow/'
UNFOLLOW_API = '/api/friendships/{}/unfollow/'
FOLLOWINGS_API = '/api/friendships/{}/followings/'
FOLLOWERS_API = '/api/friendships/{}/followers/'


class FriendshipAPITests(TestCase):
    def setUp(self):

        self.clear_cache()

        # Create users
        self.xiaohe = self.create_user('xiaohe')
        self.xiaohe_client = APIClient()
        self.xiaohe_client.force_authenticate(self.xiaohe)

        self.zhekang = self.create_user('zhekang')
        self.zhekang_client = APIClient()
        self.zhekang_client.force_authenticate(self.zhekang)

        self.chiayu = self.create_user('chiayu')
        self.chiayu_client = APIClient()
        self.chiayu_client.force_authenticate(self.chiayu)

    def test_follow_api(self):
        # Xiaohe is the user to follow
        follow_url = FOLLOW_API.format(self.xiaohe.id)

        # User must login
        response = self.anonymous_client.post(follow_url)
        self.assertEqual(response.status_code, 403)

        # Cannot follow the same person
        response = self.xiaohe_client.post(follow_url)
        self.assertEqual(response.status_code, 400)

        # GET method is not allowed
        response = self.zhekang_client.get(follow_url)
        self.assertEqual(response.status_code, 405)

        # Successful follow
        response = self.zhekang_client.post(follow_url)
        self.assertEqual(response.status_code, 201)

        # Successful duplicated follow
        response = self.zhekang_client.post(follow_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['duplicate'], True)

        # Database will be updated
        count = Friendship.objects.count()
        response = self.zhekang_client.post(FOLLOW_API.format(self.chiayu.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow_api(self):
        unfollow_url = UNFOLLOW_API.format(self.chiayu.id)
        # User must login
        response = self.anonymous_client.post(unfollow_url)
        self.assertEqual(response.status_code, 403)

        # GET method is not allowed
        response = self.zhekang_client.get(unfollow_url)
        self.assertEqual(response.status_code, 405)

        # Unable to unfollow user that has not been followed
        count = Friendship.objects.count()
        response = self.xiaohe_client.post(unfollow_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

        # Cannot unfollow the same person
        response = self.chiayu_client.post(unfollow_url)
        self.assertEqual(response.status_code, 400)

        # Successful unfollow and updates in DB
        Friendship.objects.create(from_user=self.xiaohe, to_user=self.chiayu)
        count = Friendship.objects.count()
        response = self.xiaohe_client.post(unfollow_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

    def test_followings_api(self):
        pass
        # followings_url = FOLLOWINGS_API.format{self.zhekang.id}
        #
        # # POST is not allowed
        # response = self.anonymous_client.post(followings_url)
        # self.assertEqual(response.status_code, 405)
        #
        # # Get the followings
        # response = self.anonymous_client.get(followings_url)
        # self.assertEqual(len(response.data['followings']), )

    def test_followers_api(self):
        pass

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('zhekang_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.zhekang)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.xiaohe, to_user=follower)

        url = FOLLOWERS_API.format(self.zhekang.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # xiaohe has followed users with even id
        response = self.xiaohe_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('zhekang_following{}'.format(i))
            Friendship.objects.create(from_user=self.zhekang, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.xiaohe, to_user=following)

        url = FOLLOWINGS_API.format(self.zhekang.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # xiaohe has followed users with even id
        response = self.xiaohe_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # zhekang has followed all his following users
        response = self.zhekang_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # test user can not customize page_size exceeds max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # test user can customize page size by param size
        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], page_size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)


class HBaseTests(TestCase):

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        timestamp = self.ts_now
        following = HBaseFollowing(from_user_id=123, to_user_id=34, created_at=timestamp)
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.from_user_id, 123)
        self.assertEqual(instance.to_user_id, 34)
        self.assertEqual(instance.created_at, timestamp)

        following.to_user_id = 456
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.to_user_id, 456)

        # object does not exist, return None
        instance = HBaseFollowing.get(from_user_id=123, created_at=self.ts_now)
        self.assertEqual(instance, None)

    def test_create_and_get(self):
        # missing column data, can not store in hbase
        try:
            HBaseFollower.create(to_user_id=1, created_at=self.ts_now)
            exception_raised = False
        except EmptyColumnError:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # invalid row_key
        try:
            HBaseFollower.create(from_user_id=1, to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key')
        self.assertEqual(exception_raised, True)

        ts = self.ts_now
        HBaseFollower.create(from_user_id=1, to_user_id=2, created_at=ts)
        instance = HBaseFollower.get(to_user_id=2, created_at=ts)
        self.assertEqual(instance.from_user_id, 1)
        self.assertEqual(instance.to_user_id, 2)
        self.assertEqual(instance.created_at, ts)

        # can not get if row key missing
        try:
            HBaseFollower.get(to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key')
        self.assertEqual(exception_raised, True)

    def test_filter(self):
        HBaseFollowing.create(from_user_id=1, to_user_id=2, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=3, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=4, created_at=self.ts_now)

        followings = HBaseFollowing.filter(prefix=(1, None, None))
        self.assertEqual(3, len(followings))
        self.assertEqual(followings[0].from_user_id, 1)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].from_user_id, 1)
        self.assertEqual(followings[1].to_user_id, 3)
        self.assertEqual(followings[2].from_user_id, 1)
        self.assertEqual(followings[2].to_user_id, 4)

        # test limit
        results = HBaseFollowing.filter(prefix=(1, None, None), limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].to_user_id, 2)

        results = HBaseFollowing.filter(prefix=(1, None, None), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 2)
        self.assertEqual(results[1].to_user_id, 3)

        results = HBaseFollowing.filter(prefix=(1, None, None), limit=4)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].to_user_id, 2)
        self.assertEqual(results[1].to_user_id, 3)
        self.assertEqual(results[2].to_user_id, 4)

        results = HBaseFollowing.filter(start=(1, results[1].created_at, None), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 3)
        self.assertEqual(results[1].to_user_id, 4)

        # test reverse
        results = HBaseFollowing.filter(prefix=(1, None, None), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 4)
        self.assertEqual(results[1].to_user_id, 3)

        results = HBaseFollowing.filter(start=(1, results[1].created_at, None), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 3)
        self.assertEqual(results[1].to_user_id, 2)

