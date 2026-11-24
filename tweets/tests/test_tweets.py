from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Follow
from accounts.tests.helpers import authenticate, create_user
from tweets.models import Tweet


class TweetTest(APITestCase):
    def setUp(self):
        self.maria = create_user('maria', 'Maria')
        self.joao = create_user('joao', 'João')
        authenticate(self.client, self.maria)

    def test_create_tweet(self):
        response = self.client.post(
            reverse('tweet-create'), {'content': 'Meu primeiro tweet'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Meu primeiro tweet')
        self.assertEqual(response.data['author']['username'], 'maria')
        self.assertEqual(response.data['likes_count'], 0)
        self.assertEqual(response.data['comments_count'], 0)
        self.assertEqual(Tweet.objects.count(), 1)

    def test_create_rejects_empty_content(self):
        response = self.client.post(
            reverse('tweet-create'), {'content': '   '}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tweet.objects.count(), 0)

    def test_create_rejects_content_over_280_characters(self):
        response = self.client.post(
            reverse('tweet-create'), {'content': 'a' * 281}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_retrieve_tweet(self):
        tweet = Tweet.objects.create(author=self.joao, content='Oi')

        response = self.client.get(reverse('tweet-detail', args=[tweet.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Oi')

    def test_delete_own_tweet(self):
        tweet = Tweet.objects.create(author=self.maria, content='Apagar')

        response = self.client.delete(reverse('tweet-detail', args=[tweet.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tweet.objects.count(), 0)

    def test_cannot_delete_tweet_from_another_user(self):
        tweet = Tweet.objects.create(author=self.joao, content='Do Joao')

        response = self.client.delete(reverse('tweet-detail', args=[tweet.pk]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Tweet.objects.count(), 1)

    def test_user_tweets_list(self):
        Tweet.objects.create(author=self.joao, content='Do Joao')
        Tweet.objects.create(author=self.maria, content='Da Maria')

        response = self.client.get(reverse('user-tweets', args=['joao']))

        contents = [tweet['content'] for tweet in response.data['results']]
        self.assertEqual(contents, ['Do Joao'])


class FeedTest(APITestCase):
    def setUp(self):
        self.maria = create_user('maria', 'Maria')
        self.joao = create_user('joao', 'João')
        self.ana = create_user('ana', 'Ana')
        authenticate(self.client, self.maria)

    def contents(self):
        response = self.client.get(reverse('feed'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [tweet['content'] for tweet in response.data['results']]

    def test_feed_is_empty_when_following_nobody(self):
        Tweet.objects.create(author=self.joao, content='Do Joao')

        self.assertEqual(self.contents(), [])

    def test_feed_shows_only_followed_users(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Tweet.objects.create(author=self.joao, content='Do Joao')
        Tweet.objects.create(author=self.ana, content='Da Ana')
        Tweet.objects.create(author=self.maria, content='Da Maria')

        self.assertEqual(self.contents(), ['Do Joao'])

    def test_feed_is_ordered_from_newest_to_oldest(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Follow.objects.create(follower=self.maria, followed=self.ana)
        Tweet.objects.create(author=self.joao, content='Primeiro')
        Tweet.objects.create(author=self.ana, content='Segundo')
        Tweet.objects.create(author=self.joao, content='Terceiro')

        self.assertEqual(self.contents(), ['Terceiro', 'Segundo', 'Primeiro'])

    def test_unfollow_removes_tweets_from_feed(self):
        Follow.objects.create(follower=self.maria, followed=self.joao)
        Tweet.objects.create(author=self.joao, content='Do Joao')
        self.assertEqual(self.contents(), ['Do Joao'])

        self.client.delete(reverse('follow', args=['joao']))

        self.assertEqual(self.contents(), [])
