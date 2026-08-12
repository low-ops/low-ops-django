from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from config.ready import ready
from users.pages import admin_index, admin_settings, admin_users, landing, sign_in, sign_up, verify_email
from users.permissions import IsAdmin


class PublicSchemaView(SpectacularAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class PublicSwaggerView(SpectacularSwaggerView):
    authentication_classes = []
    permission_classes = [AllowAny]


class AdminSchemaView(SpectacularAPIView):
    permission_classes = [IsAdmin]


class AdminSwaggerView(SpectacularSwaggerView):
    permission_classes = [IsAdmin]


if settings.DEBUG:
    schema_view = PublicSchemaView.as_view()
    swagger_view = PublicSwaggerView.as_view(url_name='schema')
else:
    schema_view = AdminSchemaView.as_view()
    swagger_view = AdminSwaggerView.as_view(url_name='schema')


urlpatterns = [
    path('ready', ready, name='ready'),
    path('ready/', ready, name='ready-slash'),
    path('', landing, name='landing'),
    path('auth/sign-in/', sign_in, name='sign-in-page'),
    path('auth/sign-up/', sign_up, name='sign-up-page'),
    path('auth/verify/', verify_email, name='verify-page'),
    path('admin/', admin_index, name='admin-index'),
    path('admin/users/', admin_users, name='admin-users-page'),
    path('admin/settings/', admin_settings, name='admin-settings-page'),
    path('api/', include('users.urls')),
    path('api/schema/', schema_view, name='schema'),
    path('api/docs/', swagger_view, name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
