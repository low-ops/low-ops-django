from threading import RLock

_lock = RLock()
_initialized = False


def ensure_backends():
    """Initialize DB/S3 after Django apps are fully loaded."""
    global _initialized

    if _initialized:
        return

    with _lock:
        if _initialized:
            return

        from config.database import init_database
        from storage.s3 import init_s3

        init_database()
        init_s3()
        _initialized = True
