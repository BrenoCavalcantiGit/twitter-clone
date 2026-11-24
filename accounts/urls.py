from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path(
        'users/<str:username>/',
        views.UserDetailView.as_view(),
        name='user-detail',
    ),
    path(
        'users/<str:username>/follow/',
        views.FollowView.as_view(),
        name='follow',
    ),
    path(
        'users/<str:username>/followers/',
        views.FollowersListView.as_view(),
        name='followers',
    ),
    path(
        'users/<str:username>/following/',
        views.FollowingListView.as_view(),
        name='following',
    ),
]
