from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, Q

MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB
AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']


def validate_avatar_size(file):
    if file.size > MAX_AVATAR_SIZE:
        raise ValidationError('A foto deve ter no máximo 2 MB.')


class Profile(models.Model):
    """Dados extras do usuário (foto de perfil)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.FileField(
        upload_to='avatars/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(AVATAR_EXTENSIONS),
            validate_avatar_size,
        ],
    )

    def __str__(self):
        return f'Perfil de {self.user}'


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


class Follow(models.Model):
    """Relação de seguir: follower segue followed."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_set',
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followed'], name='unique_follow'
            ),
            models.CheckConstraint(
                condition=~Q(follower=F('followed')), name='no_self_follow'
            ),
        ]

    def __str__(self):
        return f'{self.follower} segue {self.followed}'
