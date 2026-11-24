from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.tests.helpers import authenticate, create_user
from tweets.models import Comment, Like, Tweet


class LikeTest(APITestCase):
    def setUp(self):
        self.maria = create_user('maria', 'Maria')
        self.joao = create_user('joao', 'João')
        self.tweet = Tweet.objects.create(author=self.joao, content='Curta')
        self.url = reverse('tweet-like', args=[self.tweet.pk])
        authenticate(self.client, self.maria)

    def test_like_tweet(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['likes_count'], 1)
        self.assertTrue(response.data['liked_by_me'])
        self.assertEqual(Like.objects.count(), 1)

    def test_like_twice_counts_only_once(self):
        self.client.post(self.url)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['likes_count'], 1)
        self.assertEqual(Like.objects.count(), 1)

    def test_unlike_tweet(self):
        self.client.post(self.url)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['likes_count'], 0)
        self.assertFalse(response.data['liked_by_me'])
        self.assertEqual(Like.objects.count(), 0)

    def test_likes_from_different_users_are_counted(self):
        Like.objects.create(user=self.joao, tweet=self.tweet)

        response = self.client.post(self.url)

        self.assertEqual(response.data['likes_count'], 2)

    def test_like_unknown_tweet_returns_404(self):
        response = self.client.post(reverse('tweet-like', args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CommentTest(APITestCase):
    def setUp(self):
        self.maria = create_user('maria', 'Maria')
        self.joao = create_user('joao', 'João')
        self.tweet = Tweet.objects.create(author=self.joao, content='Comente')
        self.url = reverse('tweet-comments', args=[self.tweet.pk])
        authenticate(self.client, self.maria)

    def test_create_comment(self):
        response = self.client.post(
            self.url, {'content': 'Boa!'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Boa!')
        self.assertEqual(response.data['author']['username'], 'maria')
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_comment_rejects_empty_content(self):
        response = self.client.post(self.url, {'content': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 0)

    def test_list_comments_in_order(self):
        Comment.objects.create(author=self.joao, tweet=self.tweet, content='Primeiro')
        Comment.objects.create(author=self.maria, tweet=self.tweet, content='Segundo')

        response = self.client.get(self.url)

        contents = [comment['content'] for comment in response.data['results']]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(contents, ['Primeiro', 'Segundo'])

    def test_tweet_shows_comments_count(self):
        Comment.objects.create(author=self.joao, tweet=self.tweet, content='Um')
        Comment.objects.create(author=self.maria, tweet=self.tweet, content='Dois')

        response = self.client.get(reverse('tweet-detail', args=[self.tweet.pk]))

        self.assertEqual(response.data['comments_count'], 2)

    def test_comment_on_unknown_tweet_returns_404(self):
        response = self.client.post(
            reverse('tweet-comments', args=[999999]),
            {'content': 'Oi'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_comment(self):
        comment = Comment.objects.create(
            author=self.maria, tweet=self.tweet, content='Apagar'
        )

        response = self.client.delete(reverse('comment-detail', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_cannot_delete_comment_from_another_user(self):
        comment = Comment.objects.create(
            author=self.joao, tweet=self.tweet, content='Do Joao'
        )

        response = self.client.delete(reverse('comment-detail', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)
