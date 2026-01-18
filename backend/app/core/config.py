from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://outbox_user:outbox_password@localhost:5432/outbox_db"

    # Kaiten API
    KAITEN_API_URL: str
    KAITEN_API_TOKEN: str
    KAITEN_POLL_INTERVAL: int = 5
    KAITEN_USE_MOCK: bool = False  # Явно использовать mock данные вместо реального API

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # File Storage
    INCOMING_FILES_PATH: str = "/mnt/doc/Входящие"
    OUTGOING_FILES_PATH: str = "/mnt/doc/Исходящие"

    class Config:
        env_file = ".env"


settings = Settings()
