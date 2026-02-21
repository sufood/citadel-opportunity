from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tenders_username: str
    tenders_password: str
    anthropic_api_key: str = ""
    tmp_dir: Path = Path("./tmp")
    browser_headless: bool = True

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
