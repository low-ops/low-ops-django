import json
import os
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from users.auth_core import SESSION_COOKIE, create_credential_user, create_verification_token
from users.models import LoginAttempt, Session, User, Verification
from users.token_hashing import hash_token


def csrf_headers(client):
    response = client.get('/auth/sign-up/')
    if response.status_code == 302:
        client.get('/auth/sign-in/')
    token = client.cookies['csrftoken'].value
    return {'HTTP_X_CSRFTOKEN': token}


class BootstrapRegistrationTests(TestCase):
    def test_first_user_becomes_admin(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/api/auth/sign-up/',
            data=json.dumps({
                'name': 'Bootstrap Admin',
                'email': 'admin@example.com',
                'password': 'StrongPass1',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='admin@example.com')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.email_verified)

    def test_second_signup_is_rejected(self):
        create_credential_user('Admin', 'admin@example.com', 'StrongPass1', role='admin')
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/api/auth/sign-up/',
            data=json.dumps({
                'name': 'Another User',
                'email': 'other@example.com',
                'password': 'StrongPass2',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        self.assertEqual(response.status_code, 403)

    def test_sign_in_redirects_to_sign_up_when_empty(self):
        response = self.client.get('/auth/sign-in/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/auth/sign-up/')

    def test_sign_up_redirects_to_sign_in_after_bootstrap(self):
        create_credential_user('Admin', 'admin@example.com', 'StrongPass1', role='admin')
        response = self.client.get('/auth/sign-up/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/auth/sign-in/')


class AuthSecurityTests(TestCase):
    def setUp(self):
        self.user = create_credential_user(
            'Test User',
            'user@example.com',
            'StrongPass1',
            role='user',
            email_verified=True,
        )

    def test_sign_in_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/api/auth/sign-in/',
            data=json.dumps({
                'email': 'user@example.com',
                'password': 'StrongPass1',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(MAX_LOGIN_ATTEMPTS=2, LOGIN_LOCKOUT_MINUTES=15)
    def test_login_lockout_after_failed_attempts(self):
        client = Client(enforce_csrf_checks=True)
        for _ in range(2):
            response = client.post(
                '/api/auth/sign-in/',
                data=json.dumps({
                    'email': 'user@example.com',
                    'password': 'WrongPass1',
                }),
                content_type='application/json',
                **csrf_headers(client),
            )
            self.assertEqual(response.status_code, 401)

        response = client.post(
            '/api/auth/sign-in/',
            data=json.dumps({
                'email': 'user@example.com',
                'password': 'WrongPass1',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('Too many failed attempts', response.json()['error'])
        self.assertTrue(LoginAttempt.objects.filter(email='user@example.com').exists())

    def test_successful_sign_in_clears_lockout(self):
        LoginAttempt.objects.create(email='user@example.com', failures=4)
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/api/auth/sign-in/',
            data=json.dumps({
                'email': 'user@example.com',
                'password': 'StrongPass1',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LoginAttempt.objects.filter(email='user@example.com').exists())


class TokenStorageTests(TestCase):
    def test_session_token_is_hashed_in_database(self):
        client = Client(enforce_csrf_checks=True)
        create_credential_user('Admin', 'admin@example.com', 'StrongPass1', role='admin')
        response = client.post(
            '/api/auth/sign-in/',
            data=json.dumps({
                'email': 'admin@example.com',
                'password': 'StrongPass1',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        self.assertEqual(response.status_code, 200)
        raw_token = response.cookies[SESSION_COOKIE].value
        session = Session.objects.get()
        self.assertNotEqual(session.token, raw_token)
        self.assertEqual(session.token, hash_token(raw_token))

    def test_verification_token_is_hashed_in_database(self):
        create_credential_user('User', 'user@example.com', 'StrongPass1')
        raw_token = create_verification_token('user@example.com')
        record = Verification.objects.get(identifier='user@example.com')
        self.assertNotEqual(record.value, raw_token)
        self.assertEqual(record.value, hash_token(raw_token))


@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=['testserver'],
    SECRET_KEY='test-secret-key-for-tests-only-32chars',
)
class ProductionProtectionTests(TestCase):
    def setUp(self):
        self.admin = create_credential_user(
            'Admin',
            'admin@example.com',
            'StrongPass1',
            role='admin',
            email_verified=True,
        )

    def test_api_docs_require_admin_when_not_debug(self):
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 403)

        client = Client(enforce_csrf_checks=True)
        client.post(
            '/api/auth/sign-in/',
            data=json.dumps({
                'email': 'admin@example.com',
                'password': 'StrongPass1',
            }),
            content_type='application/json',
            **csrf_headers(client),
        )
        response = client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)

    def test_metrics_auth_helper(self):
        from config.metrics import is_metrics_authorized

        with patch.dict(os.environ, {'METRICS_AUTH_TOKEN': 'secret-token'}, clear=False):
            authorized = is_metrics_authorized({
                'HTTP_AUTHORIZATION': 'Bearer secret-token',
            })
            self.assertTrue(authorized)

            unauthorized = is_metrics_authorized({
                'HTTP_AUTHORIZATION': 'Bearer wrong-token',
            })
            self.assertFalse(unauthorized)
