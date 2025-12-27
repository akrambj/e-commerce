from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    env: str = Field(default="development", alias="ENV")
    app_name: str = Field(default="E-commerce Platform", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    version: str = Field(default="1.0.0", alias="VERSION")
    database_url: str = Field(..., alias="DATABASE_URL")



@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore