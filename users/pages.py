from django.shortcuts import render


def home(request):
    return render(request, 'users/home.html')


def detail(request, user_id):
    return render(request, 'users/detail.html', {'user_id': user_id})
