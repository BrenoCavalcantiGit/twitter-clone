from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Follow

from .helpers import authenticate, create_user


class FollowTest(APITestCase):
    def setUp(self):
        self.maria = create_user('maria', 'Maria')
        self.joao = create_user('joao', 'João')
        self.ana = create_user('ana', 'Ana')
        authenticate(self.client, self.maria)

    def follow_url(self, username):
        return reverse('follow', args=[username])

    def test_follow_user(self):
        response = self.client.post(self.follow_url('joao'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.maria, followed=self.joao).exists()
        )
        self.assertTrue(response.data['is_following'])

    def test_follow_twice_does_not_duplicate(self):
        self.client.post(self.follow_url('joao'))

        response = self.client.post(self.follow_url('joao'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 1)

    def test_cannot_follow_yourself(self):
        response = self.client.post(self.follow_url('maria'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_unknown_user_returns_404(self):
        response = self.client.post(self.follow_url('ninguem'))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unfollow_user(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)

        response = self.client.delete(self.follow_url('joao'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Follow.objects.count(), 0)

    def test_user_detail_shows_counts_and_follow_state(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Follow.objects.create(follower=self.ana, followed=self.joao)
        Follow.objects.create(follower=self.joao, followed=self.ana)

        response = self.client.get(reverse('user-detail', args=['joao']))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['followers_count'], 2)
        self.assertEqual(response.data['following_count'], 1)
        self.assertTrue(response.data['is_following'])

    def test_followers_list(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Follow.objects.create(follower=self.ana, followed=self.joao)

        response = self.client.get(reverse('followers', args=['joao']))

        usernames = [user['username'] for user in response.data['results']]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(usernames, ['ana', 'maria'])

    def test_following_list(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Follow.objects.create(follower=self.maria, followed=self.ana)
        Follow.objects.create(follower=self.joao, followed=self.ana)

        response = self.client.get(reverse('following', args=['maria']))

        usernames = [user['username'] for user in response.data['results']]
        self.assertEqual(usernames, ['ana', 'joao'])

    def test_user_list_can_be_searched(self):
        response = self.client.get(reverse('user-list'), {'q': 'jo'})

        usernames = [user['username'] for user in response.data['results']]
        self.assertEqual(usernames, ['joao'])
