from typing import Optional

from config import settings


def authenticate(auth_token: Optional[str]):
    if not auth_token:
        return False

    if auth_token and auth_token == settings.auth_token:
        return True

    return False
