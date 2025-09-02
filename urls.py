from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def hello_view(request):
    return HttpResponse("Hello from Low-Ops Django Template")

urlpatterns = [
    path('', hello_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 