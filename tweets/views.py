from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, Like, Tweet
from .serializers import CommentSerializer, TweetSerializer

User = get_user_model()


def tweet_data(tweet_id, request):
    tweet = Tweet.objects.with_counts().get(pk=tweet_id)
    return TweetSerializer(tweet, context={'request': request}).data


class TweetCreateView(generics.CreateAPIView):
    serializer_class = TweetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tweet = serializer.save(author=request.user)

        return Response(
            tweet_data(tweet.pk, request), status=status.HTTP_201_CREATED
        )


class TweetDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = TweetSerializer

    def get_queryset(self):
        return Tweet.objects.with_counts()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                'Você só pode apagar os seus próprios tweets.'
            )
        instance.delete()


class UserTweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Tweet.objects.with_counts().filter(author=user)


class FeedView(generics.ListAPIView):
    """Feed: só os tweets de quem o usuário segue, do mais novo ao mais antigo."""

    serializer_class = TweetSerializer

    def get_queryset(self):
        return Tweet.objects.with_counts().filter(
            author__followers_set__follower=self.request.user
        )


class LikeView(APIView):
    def post(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)
        _, created = Like.objects.get_or_create(user=request.user, tweet=tweet)

        return Response(
            tweet_data(tweet.pk, request),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)
        Like.objects.filter(user=request.user, tweet=tweet).delete()

        return Response(tweet_data(tweet.pk, request))


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs['pk'])

    def get_queryset(self):
        return Comment.objects.filter(tweet=self.get_tweet()).select_related(
            'author', 'author__profile'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, tweet=self.get_tweet())


class CommentDetailView(generics.DestroyAPIView):
    queryset = Comment.objects.all()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                'Você só pode apagar os seus próprios comentários.'
            )
        instance.delete()
