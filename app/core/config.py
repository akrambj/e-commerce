from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # existing
    env: str = Field(default="development", alias="ENV")
    app_name: str = Field(default="E-commerce Platform", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    version: str = Field(default="1.0.0", alias="VERSION")

    database_url: str = Field(..., alias="DATABASE_URL")
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    # google sheets
    google_sheets_spreadsheet_id: str = Field(..., alias="GOOGLE_SHEETS_SPREADSHEET_ID")
    google_sheets_sheet_name: str = Field(..., alias="GOOGLE_SHEETS_SHEET_NAME")
    google_service_account_json_b64: str = Field(..., alias="GOOGLE_SERVICE_ACCOUNT_JSON_B64")

    # ✅ admin auth (Step 23.1)
    admin_email: str = Field(..., alias="ADMIN_EMAIL")
    admin_password: str = Field(..., alias="ADMIN_PASSWORD")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_access_token_expires_minutes: int = Field(
        default=60,
        alias="JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
    )

    cloudinary_cloud_name: str = Field(..., alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(..., alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(..., alias="CLOUDINARY_API_SECRET")

    cloudinary_products_folder: str = Field(
    default="purity/products",
    alias="CLOUDINARY_PRODUCTS_FOLDER",
    )   



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings() # type: ignore
