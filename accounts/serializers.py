from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from .models import AVATAR_EXTENSIONS, Follow, validate_avatar_size

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """Versão resumida do usuário, usada dentro de tweets e comentários."""

    name = serializers.CharField(source='first_name', read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar']

    def get_avatar(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile and profile.avatar:
            return profile.avatar.url
        return None


class UserSerializer(AuthorSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta(AuthorSerializer.Meta):
        fields = AuthorSerializer.Meta.fields + [
            'followers_count',
            'following_count',
            'is_following',
        ]

    def get_followers_count(self, obj):
        return obj.followers_set.count()

    def get_following_count(self, obj):
        return obj.following_set.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(
            follower=request.user, followed=obj
        ).exists()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150, validators=[UnicodeUsernameValidator()]
    )
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'}
    )
    name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'Este nome de usuário já está em uso.'
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('name', ''),
        )


class ProfileUpdateSerializer(serializers.Serializer):
    """Todos os campos são opcionais: o usuário altera só o que quiser."""

    name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    avatar = serializers.FileField(
        required=False,
        validators=[
            FileExtensionValidator(AVATAR_EXTENSIONS),
            validate_avatar_size,
        ],
    )
    remove_avatar = serializers.BooleanField(required=False)
    current_password = serializers.CharField(required=False, write_only=True)
    new_password = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        current = attrs.get('current_password')
        new = attrs.get('new_password')

        if current or new:
            if not current or not new:
                raise serializers.ValidationError(
                    {'new_password': 'Informe a senha atual e a nova senha.'}
                )

            user = self.context['request'].user
            if not user.check_password(current):
                raise serializers.ValidationError(
                    {'current_password': 'A senha atual está incorreta.'}
                )

            validate_password(new, user=user)

        return attrs
