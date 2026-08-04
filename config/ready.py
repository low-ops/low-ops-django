from django.http import HttpResponse


def ready(request):
    return HttpResponse('ok', content_type='text/plain')
