from django.conf import settings
from django.db import models
from django.db.models import Count


class TweetQuerySet(models.QuerySet):
    def with_counts(self):
        """Traz o autor e as contagens de curtidas e comentários."""
        return self.select_related('author', 'author__profile').annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )


class Tweet(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tweets',
    )
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TweetQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.author}: {self.content[:30]}'


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    tweet = models.ForeignKey(
        Tweet, on_delete=models.CASCADE, related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tweet'], name='unique_like'
            ),
        ]


class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    tweet = models.ForeignKey(
        Tweet, on_delete=models.CASCADE, related_name='comments'
    )
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.author}: {self.content[:30]}'
