import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import get_profile

from .helpers import PASSWORD, authenticate, create_user

MEDIA_DIR = tempfile.mkdtemp()
NEW_PASSWORD = 'NovaSenha#2027'


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class ProfileTest(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.url = reverse('me')
        self.user = create_user('maria', 'Maria')
        self.token = authenticate(self.client, self.user)

    def test_get_returns_own_profile(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'maria')
        self.assertEqual(response.data['name'], 'Maria')
        self.assertIsNone(response.data['avatar'])

    def test_empty_update_changes_nothing(self):
        response = self.client.patch(self.url, {}, format='json')

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, 'Maria')
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_update_only_name(self):
        response = self.client.patch(
            self.url, {'name': 'Maria Souza'}, format='json'
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['name'], 'Maria Souza')
        self.assertEqual(self.user.first_name, 'Maria Souza')
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_upload_avatar(self):
        photo = SimpleUploadedFile(
            'foto.png', b'conteudo-da-imagem', content_type='image/png'
        )

        response = self.client.patch(
            self.url, {'avatar': photo}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data['user']['avatar'].startswith('/media/avatars/')
        )
        self.assertTrue(get_profile(self.user).avatar)

    def test_avatar_with_invalid_extension_is_rejected(self):
        file = SimpleUploadedFile('virus.exe', b'conteudo')

        response = self.client.patch(
            self.url, {'avatar': file}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_avatar_too_big_is_rejected(self):
        file = SimpleUploadedFile(
            'grande.png', b'x' * (2 * 1024 * 1024 + 1), content_type='image/png'
        )

        response = self.client.patch(
            self.url, {'avatar': file}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_remove_avatar(self):
        photo = SimpleUploadedFile('foto.png', b'conteudo', content_type='image/png')
        self.client.patch(self.url, {'avatar': photo}, format='multipart')

        response = self.client.patch(
            self.url, {'remove_avatar': True}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['user']['avatar'])
        self.assertFalse(get_profile(self.user).avatar)

    def test_change_password(self):
        response = self.client.patch(
            self.url,
            {'current_password': PASSWORD, 'new_password': NEW_PASSWORD},
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertIn('token', response.data)
        self.assertNotEqual(response.data['token'], self.token.key)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_change_password_rejects_wrong_current_password(self):
        response = self.client.patch(
            self.url,
            {'current_password': 'errada', 'new_password': NEW_PASSWORD},
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_change_password_requires_both_passwords(self):
        response = self.client.patch(
            self.url, {'new_password': NEW_PASSWORD}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_change_password_rejects_weak_new_password(self):
        response = self.client.patch(
            self.url,
            {'current_password': PASSWORD, 'new_password': '123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
