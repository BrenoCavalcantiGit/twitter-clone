from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Follow, get_profile
from .serializers import (
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def user_data(user, request):
    return UserSerializer(user, context={'request': request}).data


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {'token': token.key, 'user': user_data(user, request)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AuthTokenSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key, 'user': user_data(user, request)})


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(user_data(request.user, request))

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        profile = get_profile(user)

        if 'name' in data:
            user.first_name = data['name']

        new_password = data.get('new_password')
        if new_password:
            user.set_password(new_password)

        user.save()

        if data.get('remove_avatar'):
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save()

        if 'avatar' in data:
            profile.avatar = data['avatar']
            profile.save()

        response = {'user': user_data(user, request)}

        if new_password:
            # Troca o token por segurança: o antigo deixa de valer
            Token.objects.filter(user=user).delete()
            response['token'] = Token.objects.create(user=user).key

        return Response(response)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.select_related('profile').order_by('username')
        term = self.request.query_params.get('q', '').strip()

        if term:
            queryset = queryset.filter(
                Q(username__icontains=term) | Q(first_name__icontains=term)
            )

        return queryset


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.select_related('profile')
    lookup_field = 'username'


class FollowView(APIView):
    def post(self, request, username):
        target = get_object_or_404(User, username=username)

        if target == request.user:
            return Response(
                {'detail': 'Você não pode seguir a si mesmo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        _, created = Follow.objects.get_or_create(
            follower=request.user, followed=target
        )

        return Response(
            user_data(target, request),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, username):
        target = get_object_or_404(User, username=username)
        Follow.objects.filter(follower=request.user, followed=target).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        target = get_object_or_404(User, username=self.kwargs['username'])

        return (
            User.objects.filter(following_set__followed=target)
            .select_related('profile')
            .order_by('username')
        )


class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        target = get_object_or_404(User, username=self.kwargs['username'])

        return (
            User.objects.filter(followers_set__follower=target)
            .select_related('profile')
            .order_by('username')
        )
