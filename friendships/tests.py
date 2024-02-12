from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.services import FriendshipServices


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user('zhekang')
        self.xiaohe = self.create_user('xiaohe')

    def test_get_followings(self):
        user_1 = self.create_user('user_1')
        user_2 = self.create_user('user_2')
        for to_user in [user_1, user_2, self.xiaohe]:
            Friendship.objects.create(from_user=self.zhekang, to_user=to_user)

        user_id_set = FriendshipServices.get_following_user_id_set(self.zhekang.id)
        self.assertEqual(user_id_set, {user_1.id, user_2.id, self.xiaohe.id})

        # Unfollow one user
        Friendship.objects.filter(from_user=self.zhekang, to_user=user_1).delete()
        user_id_set = FriendshipServices.get_following_user_id_set(self.zhekang.id)
        self.assertEqual(user_id_set, {user_2.id, self.xiaohe.id})
