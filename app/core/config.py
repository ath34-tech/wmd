from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./wmd.db"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 5 * 1024 * 1024


settings = Settings()
