from users.models import User


def is_registration_open():
    return not User.objects.exists()
