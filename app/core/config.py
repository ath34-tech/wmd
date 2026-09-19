from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./wmd.db"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"


settings = Settings()
