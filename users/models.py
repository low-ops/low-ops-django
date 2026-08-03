from django.db import models


class User(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    avatar = models.TextField(blank=True, null=True)
    avatar_key = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['id']

    def __str__(self):
        return self.name
