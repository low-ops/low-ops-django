#!/usr/bin/env python
import os
import sys

from config.dotenv import load_dotenv_file

if __name__ == "__main__":
    load_dotenv_file()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv) 