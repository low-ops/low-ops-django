from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.auth_core import (
    attach_session_cookie,
    clear_session,
    create_credential_user,
    create_verification_token,
    revoke_user_sessions,
    serialize_user,
    sign_in_with_password,
    validate_password,
    verify_email_token,
)
from users.csrf import enforce_csrf
from users.models import User
from users.permissions import IsAuthenticated
from users.registration import is_registration_open
from users.services.email import send_verification_email


class SignInView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        email = request.data.get('email', '')
        password = request.data.get('password', '')
        result, error = sign_in_with_password(request, email, password)
        if error:
            return Response({'error': error}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'user': serialize_user(result['user'])})
        attach_session_cookie(response, result['token'])
        return response


class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        if not is_registration_open():
            return Response({'error': 'Sign up is disabled.'}, status=403)

        name = (request.data.get('name') or '').strip()
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        if not name or not email or not password:
            return Response({'error': 'Name, email, and password are required.'}, status=400)

        password_error = validate_password(password)
        if password_error:
            return Response({'error': password_error}, status=400)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'An account with this email already exists.'}, status=400)

        email_verified = not settings.EMAIL_VERIFICATION_ENABLED
        user = create_credential_user(
            name,
            email,
            password,
            email_verified=email_verified,
            role='admin',
        )

        if settings.EMAIL_VERIFICATION_ENABLED:
            token = create_verification_token(user.email)
            verify_url = f'{settings.APPLICATION_URL}/auth/verify/?token={token}'
            send_verification_email(user, verify_url)

        return Response({'user': serialize_user(user)}, status=201)


class SignOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({'success': True})
        clear_session(request, response)
        return response


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': serialize_user(request.user_obj)})


class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        token = request.data.get('token') or request.query_params.get('token')
        user, error = verify_email_token(token)
        if error:
            return Response({'error': error}, status=400)
        return Response({'user': serialize_user(user)})


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user_obj
        name = request.data.get('name')
        image = request.data.get('image')

        fields = []
        if name is not None:
            name = str(name).strip()
            if len(name) < 2:
                return Response({'error': 'Name must be at least 2 characters.'}, status=400)
            user.name = name
            fields.append('name')

        if image is not None:
            user.image = image or None
            fields.append('image')

        if fields:
            user.save(update_fields=fields + ['updated_at'])

        return Response({'user': serialize_user(user)})


class RevokeSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from users.auth_core import is_admin_role

        actor = request.user_obj
        if actor.id != user_id and not is_admin_role(actor.role):
            return Response({'error': 'Forbidden'}, status=403)

        except_token = request.COOKIES.get('session_token') if actor.id == user_id else None
        count = revoke_user_sessions(user_id, except_token=except_token)
        return Response({'revoked': count})
