from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship

LIST_API = '/api/friendships/'
FOLLOW_API = '/api/friendships/{}/follow/'
UNFOLLOW_API = '/api/friendships/{}/unfollow/'
FOLLOWINGS_API = '/api/friendships/{}/followings/'
FOLLOWERS_API = '/api/friendships/{}/followers/'

class FriendshipAPITests(TestCase):
    def setUp(self):
        # Create users
        self.anonymous_client = APIClient()

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





