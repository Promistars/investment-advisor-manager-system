from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

IAMS_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(IAMS_ROOT / ".env"), extra="ignore")

    app_name: str = "IAMS"
    app_version: str = "2.1.2"
    mount_path: str = "/IAMS"
    secret_key: str = "iams-change-me-in-production-use-env"
    access_token_expire_minutes: int = 60 * 24 * 7
    cookie_name: str = "iams_token"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    data_root: Path = IAMS_ROOT


settings = Settings()
