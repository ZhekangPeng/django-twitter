from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'

class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.createUser(
            username='Zach',
            email='pzk0417@gmail.com',
            password='pzk619859065',
        )

    def createUser(self, username, email, password):
        return User.objects.create_user(username, email, password)

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
            'password': "pzk619859065",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], self.user.email)

        # Test user has logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


    def test_logout(self):
        # User logs in first
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': "pzk619859065",
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

        # Test user name is too long
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

        # Test user is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)



