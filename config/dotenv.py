import os
from pathlib import Path


def load_dotenv_file():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.is_file():
        load_dotenv(env_path)
