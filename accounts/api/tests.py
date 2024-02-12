from rest_framework.test import APIClient
from testing.testcases import TestCase
from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.client = APIClient()
        self.user = self.create_user(
            username='Zach',
            email='pzk0417@gmail.com',
            password='correctpw',
        )

    def test_login(self):
        # Test GET method is not allowed
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': self.user.password,
        })
        self.assertEqual(response.status_code, 405)

        # Test Wrong password is provided
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'some_password'
        })
        self.assertEqual(response.status_code, 400)

        # Test user is not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # Test correct credential is provided
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': "correctpw",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['id'], self.user.id)

        # Test user has logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # User logs in first
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': "correctpw",
        })

        # Test user is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # Test GET is not allowed
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # Logout user by POST
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # Test User is not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'new_user',
            'email': 'new_email@gmail.com',
            'password': 'new_password',
        }
        # Test GET is not allowed
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # Test email is not valid
        response = self.client.post(SIGNUP_URL, {
            'username': 'random_user',
            'email': 'not a valid email',
            'password': 'random_password',
        })
        self.assertEqual(response.status_code, 400)

        # Test username is too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'abc',
            'email': 'validemail@gmail.com',
            'password': 'valid_password',
        })
        self.assertEqual(response.status_code, 400)

        # Test password is too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'random_user',
            'email': 'someone@gmail.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, 400)

        # Test username is too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'abcabcabcabcabcabcabcaabcabcabcb',
            'email': 'validemail@gmail.com',
            'password': 'valid_password',
        })
        self.assertEqual(response.status_code, 400)

        # Signup is completed
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], data['username'])
        # User profile is created
        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertEqual(isinstance(profile, UserProfile), True)

        # Test user is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileAPITests(TestCase):
    def test_update(self):
        zhekang, zhekang_client = self.create_user_and_client('zhekang')
        profile = zhekang.profile
        profile.nickname = 'old nickname'
        profile.save()
        url = USER_PROFILE_DETAIL_URL.format(profile.id)

        # Only the profile owner can update it
        _, xiaohe_client = self.create_user_and_client('xiaohe')
        response = xiaohe_client.put(url, {'nickname': "new nickname"})
        self.assertEqual(response.status_code, 403)
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, "old nickname")

        # Update nickname
        response = zhekang_client.put(url, {'nickname': "new nickname"})
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, "new nickname")

        # Update avatar
        response = zhekang_client.put(url, {
            'avatar': SimpleUploadedFile(
                name="avatar_image.jpg",
                content=str.encode('a fake image'),
                content_type='image/jpeg',
            )
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('avatar_image' in response.data['avatar'], True)
        profile.refresh_from_db()
        self.assertIsNotNone(profile.avatar)

