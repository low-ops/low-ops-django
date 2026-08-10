from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.auth_core import create_credential_user, create_verification_token, validate_password
from users.models import User
from users.permissions import IsAdmin
from users.services.email import is_email_verification_enabled, send_verification_email
from users.services.users import (
    ban_user,
    delete_user_record,
    get_users,
    set_user_role,
    unban_user,
)
from users.auth_core import revoke_user_sessions


class AdminUsersListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        page = max(int(request.query_params.get('page', 1)), 1)
        limit = min(max(int(request.query_params.get('limit', 10)), 1), 100)
        offset = (page - 1) * limit

        sort_direction = request.query_params.get('sortDirection')
        if sort_direction not in {'asc', 'desc'}:
            sort_direction = 'desc'

        result = get_users(
            limit=limit,
            offset=offset,
            sort_by=request.query_params.get('sortBy'),
            sort_direction=sort_direction,
            role=request.query_params.get('role'),
            status=request.query_params.get('status'),
            email=request.query_params.get('email'),
            name=request.query_params.get('name'),
        )

        users = []
        for user in result['users']:
            users.append({
                **user,
                'banExpires': user['banExpires'].isoformat() if user['banExpires'] else None,
                'lastSignIn': user['lastSignIn'].isoformat() if user['lastSignIn'] else None,
                'createdAt': user['createdAt'].isoformat(),
            })

        total = result['total']
        total_pages = max((total + limit - 1) // limit, 1)
        return Response({
            'users': users,
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': total_pages,
        })


class AdminUserCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''
        role = request.data.get('role') or 'user'
        auto_verify = bool(request.data.get('autoVerify'))

        if not name or not email or not password:
            return Response({'error': 'Name, email, and password are required.'}, status=400)

        password_error = validate_password(password)
        if password_error:
            return Response({'error': password_error}, status=400)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'An account with this email already exists.'}, status=400)

        from django.conf import settings

        email_verified = auto_verify or not settings.EMAIL_VERIFICATION_ENABLED
        user = create_credential_user(
            name,
            email,
            password,
            email_verified=email_verified,
            role=role,
        )

        if settings.EMAIL_VERIFICATION_ENABLED and not auto_verify:
            token = create_verification_token(user.email)
            verify_url = f'{settings.APPLICATION_URL}/auth/verify/?token={token}'
            send_verification_email(user, verify_url)

        return Response({'id': user.id}, status=201)


class AdminUserBanView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        reason = request.data.get('banReason') or request.data.get('reason') or ''
        ban_expires_in = request.data.get('banExpiresIn')
        if ban_expires_in is not None:
            ban_expires_in = int(ban_expires_in)
        ban_user(user_id, reason, ban_expires_in)
        return Response({'success': True})


class AdminUserUnbanView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        unban_user(user_id)
        return Response({'success': True})


class AdminUserRoleView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        role = request.data.get('role')
        if role not in {'user', 'admin'}:
            return Response({'error': 'Invalid role.'}, status=400)
        set_user_role(user_id, role)
        return Response({'success': True})


class AdminUserDeleteView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, user_id):
        if request.user_obj.id == user_id:
            return Response({'error': 'You cannot delete your own account.'}, status=400)
        delete_user_record(user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserRevokeSessionsView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        count = revoke_user_sessions(user_id)
        return Response({'revoked': count})
