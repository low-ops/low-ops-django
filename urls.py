from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.ready import ready
from users.pages import admin_index, admin_settings, admin_users, landing, sign_in, sign_up, verify_email

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
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
