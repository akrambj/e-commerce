from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    env: str = Field(default="development", alias="ENV")
    app_name: str = Field(default="E-commerce Platform", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    version: str = Field(default="1.0.0", alias="VERSION")

settings = Settings()