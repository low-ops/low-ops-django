import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from users.models import Account, Session, User

FIRST_NAMES = [
    'Alice', 'Bob', 'Carol', 'David', 'Emma', 'Frank', 'Grace', 'Henry',
    'Ivy', 'Jack', 'Kate', 'Leo', 'Mia', 'Noah', 'Olivia', 'Paul',
]
LAST_NAMES = [
    'Johnson', 'Smith', 'Lee', 'Brown', 'Wilson', 'Taylor', 'Anderson', 'Thomas',
    'Jackson', 'White', 'Harris', 'Martin', 'Garcia', 'Martinez', 'Robinson', 'Clark',
]

MOCK_USER_COUNT = 50
ADMIN_EMAIL = 'admin@gmail.com'
ADMIN_PASSWORD = 'admin'


def email_password(email):
    return email.split('@', 1)[0]


def skip_if_exists(email):
    return User.objects.filter(email__iexact=email).exists()


def create_credential_user(*, name, email, password, role='user', email_verified=True, **extra):
    user = User.objects.create(
        name=name,
        email=email,
        email_verified=email_verified,
        role=role,
        **extra,
    )
    Account.objects.create(
        account_id=email,
        provider_id='credential',
        user=user,
        password=make_password(password),
    )
    return user


class Command(BaseCommand):
    help = 'Seed the database with mock users for development'

    def handle(self, *args, **options):
        connection.ensure_connection()
        call_command('migrate', '--noinput', '--fake-initial', verbosity=0)

        created = 0
        skipped = 0

        if skip_if_exists(ADMIN_EMAIL):
            self.stdout.write(f'Skipping existing user: {ADMIN_EMAIL}')
            skipped += 1
        else:
            create_credential_user(
                name='Admin User',
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                role='admin',
            )
            created += 1

        for index in range(MOCK_USER_COUNT):
            first = FIRST_NAMES[index % len(FIRST_NAMES)]
            last = LAST_NAMES[(index // len(FIRST_NAMES)) % len(LAST_NAMES)]
            email = f'{first.lower()}.{last.lower()}{index}@example.com'

            if skip_if_exists(email):
                skipped += 1
                continue

            verified = index % 3 != 0
            banned = index % 17 == 0
            ban_expires = timezone.now() + timedelta(days=7) if index % 23 == 0 else None

            user = create_credential_user(
                name=f'{first} {last}',
                email=email,
                password=email_password(email),
                role='user',
                email_verified=verified,
                banned=banned,
                ban_reason='Spamming' if banned else None,
                ban_expires=ban_expires if banned else None,
            )
            created += 1

            if index % 4 == 0:
                Session.objects.create(
                    token=secrets.token_urlsafe(32),
                    expires_at=timezone.now() + timedelta(days=7),
                    user=user,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {created} created, {skipped} skipped '
                f'({ADMIN_EMAIL} / {ADMIN_PASSWORD}).'
            )
        )
