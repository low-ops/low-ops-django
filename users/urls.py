from django.urls import path

from .views.admin_api import (
    AdminUserBanView,
    AdminUserCreateView,
    AdminUserDeleteView,
    AdminUserRevokeSessionsView,
    AdminUserRoleView,
    AdminUserUnbanView,
    AdminUsersListView,
)
from .views.auth_api import (
    RevokeSessionsView,
    SessionView,
    SignInView,
    SignOutView,
    SignUpView,
    UpdateProfileView,
    VerifyEmailView,
)
from .views.avatar_api import AvatarServeView, AvatarUploadView

urlpatterns = [
    path('auth/sign-in/', SignInView.as_view(), name='auth-sign-in'),
    path('auth/sign-up/', SignUpView.as_view(), name='auth-sign-up'),
    path('auth/sign-out/', SignOutView.as_view(), name='auth-sign-out'),
    path('auth/session/', SessionView.as_view(), name='auth-session'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('user/profile/', UpdateProfileView.as_view(), name='user-profile'),
    path('user/avatar/', AvatarUploadView.as_view(), name='user-avatar-upload'),
    path('user/avatar/<str:user_id>/', AvatarServeView.as_view(), name='user-avatar-serve'),
    path('admin/users/', AdminUsersListView.as_view(), name='admin-users-list'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin-users-create'),
    path('admin/users/<str:user_id>/ban/', AdminUserBanView.as_view(), name='admin-user-ban'),
    path('admin/users/<str:user_id>/unban/', AdminUserUnbanView.as_view(), name='admin-user-unban'),
    path('admin/users/<str:user_id>/role/', AdminUserRoleView.as_view(), name='admin-user-role'),
    path('admin/users/<str:user_id>/', AdminUserDeleteView.as_view(), name='admin-user-delete'),
    path('admin/users/<str:user_id>/revoke-sessions/', AdminUserRevokeSessionsView.as_view(), name='admin-user-revoke'),
    path('auth/revoke-sessions/<str:user_id>/', RevokeSessionsView.as_view(), name='auth-revoke-sessions'),
]
