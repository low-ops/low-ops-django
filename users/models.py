import uuid

from django.db import models


def generate_id():
    return str(uuid.uuid4())


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_id, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    image = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True, default='user')
    banned = models.BooleanField(blank=True, null=True, default=False)
    ban_reason = models.TextField(blank=True, null=True)
    ban_expires = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Session(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_id, editable=False)
    expires_at = models.DateTimeField()
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='sessions')
    impersonated_by = models.CharField(max_length=36, blank=True, null=True)

    class Meta:
        db_table = 'session'


class Account(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_id, editable=False)
    account_id = models.CharField(max_length=255)
    provider_id = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='accounts')
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    id_token = models.TextField(blank=True, null=True)
    access_token_expires_at = models.DateTimeField(blank=True, null=True)
    refresh_token_expires_at = models.DateTimeField(blank=True, null=True)
    scope = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account'


class Verification(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_id, editable=False)
    identifier = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'verification'
