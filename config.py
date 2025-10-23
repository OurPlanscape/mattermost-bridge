from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "mattermost-bridge"


settings = Settings()
