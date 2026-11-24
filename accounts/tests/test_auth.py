from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .helpers import PASSWORD, authenticate, create_user

User = get_user_model()


class RegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('register')
        self.data = {
            'username': 'maria',
            'password': PASSWORD,
            'name': 'Maria Silva',
        }

    def test_register_creates_user_and_returns_token(self):
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'maria')
        self.assertEqual(response.data['user']['name'], 'Maria Silva')

    def test_password_is_stored_hashed(self):
        self.client.post(self.url, self.data, format='json')

        user = User.objects.get(username='maria')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)

    def test_register_without_name(self):
        data = dict(self.data)
        data.pop('name')

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['name'], '')

    def test_register_rejects_duplicated_username(self):
        create_user('maria')
        data = dict(self.data, username='MARIA')

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_rejects_weak_password(self):
        data = dict(self.data, password='123')

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username='maria').exists())

    def test_register_requires_username_and_password(self):
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)


class LoginLogoutTest(APITestCase):
    def setUp(self):
        self.user = create_user('maria', 'Maria')

    def test_login_returns_token(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'maria', 'password': PASSWORD},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'maria')

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'maria', 'password': 'senha-errada'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_login_ignores_an_old_invalid_token_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token token-invalido')

        response = self.client.post(
            reverse('login'),
            {'username': 'maria', 'password': PASSWORD},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_deletes_the_token(self):
        token = authenticate(self.client, self.user)

        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token.key).exists())

        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthRequiredTest(APITestCase):
    def test_protected_endpoints_require_token(self):
        urls = [
            reverse('me'),
            reverse('user-list'),
            reverse('feed'),
            reverse('tweet-create'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED, url
            )
