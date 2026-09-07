from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    postgres_db: str = "qa_visual"
    postgres_user: str = "qa_visual"
    postgres_password: str = ""
    database_host: str = "127.0.0.1"
    database_port: int = 5433
    storage_root: str = "storage/local"

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg", username=self.postgres_user,
            password=self.postgres_password, host=self.database_host,
            port=self.database_port, database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
