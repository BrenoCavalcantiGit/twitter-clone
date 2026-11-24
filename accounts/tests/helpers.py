from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

PASSWORD = 'SenhaForte#2026'


def create_user(username, name=''):
    return User.objects.create_user(
        username=username, password=PASSWORD, first_name=name
    )


def authenticate(client, user):
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    return token
