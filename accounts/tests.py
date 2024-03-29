from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTests(TestCase):

    def test_profile_property(self):
        self.clear_cache()
        zhekang = self.create_user('zhekang')
        self.assertEqual(UserProfile.objects.count(), 0)
        p = zhekang.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)
