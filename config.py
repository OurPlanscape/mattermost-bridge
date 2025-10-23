import logging
from typing import Optional

from pydantic_settings import BaseSettings


def configure_logging(level):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class Settings(BaseSettings):
    app_name: str = "mattermost-bridge"
    log_level: str = "INFO"
    auth_token: Optional[str] = None


settings = Settings()
