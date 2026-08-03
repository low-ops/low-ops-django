from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from django.conf import settings

        from config.database import init_database
        from storage.s3 import init_s3
        from users.store import log_backend_mode

        init_database(settings.BASE_DIR)
        init_s3()
        log_backend_mode()
