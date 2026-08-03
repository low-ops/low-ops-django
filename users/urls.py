from django.urls import path

from .views import UserAvatarView, UserDetailView, UserListCreateView

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:user_id>/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]
