from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from users.pages import detail, home

urlpatterns = [
    path('', home, name='home'),
    path('users/<int:user_id>/', detail, name='user-detail-page'),
    path('api/users/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
