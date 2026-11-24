from django.urls import path

from . import views

urlpatterns = [
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('tweets/', views.TweetCreateView.as_view(), name='tweet-create'),
    path(
        'tweets/<int:pk>/',
        views.TweetDetailView.as_view(),
        name='tweet-detail',
    ),
    path(
        'tweets/<int:pk>/like/',
        views.LikeView.as_view(),
        name='tweet-like',
    ),
    path(
        'tweets/<int:pk>/comments/',
        views.CommentListCreateView.as_view(),
        name='tweet-comments',
    ),
    path(
        'comments/<int:pk>/',
        views.CommentDetailView.as_view(),
        name='comment-detail',
    ),
    path(
        'users/<str:username>/tweets/',
        views.UserTweetsView.as_view(),
        name='user-tweets',
    ),
]
