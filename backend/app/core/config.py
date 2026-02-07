from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://outbox_user:outbox_password@localhost:5432/outbox_db"

    # Kaiten API
    KAITEN_API_URL: str
    KAITEN_API_TOKEN: str
    KAITEN_POLL_INTERVAL: int = 5
    KAITEN_USE_MOCK: bool = False

    # Kaiten Board and Column IDs
    KAITEN_BOARD_ID: int
    KAITEN_LANE_ID: int
    KAITEN_COLUMN_TO_SIGN_ID: int
    KAITEN_COLUMN_OUTBOX_ID: int
    KAITEN_COLUMN_HEAD_REVIEW_ID: int
    KAITEN_COLUMN_REWORK_ID: int  # Колонка для возврата на доработку (для директора)
    KAITEN_COLUMN_KIROV_71_ID: int  # Колонка "На подпись Кирова 71"

    # Kaiten Properties
    KAITEN_PROPERTY_INCOMING_NO: str
    KAITEN_PROPERTY_INCOMING_DATE: str
    KAITEN_PROPERTY_OUTGOING_NO: str
    KAITEN_PROPERTY_OUTGOING_DATE: str
    KAITEN_PROPERTY_CONTENT: str = "id_475860"  # Краткое содержание

    # Kaiten Tags
    KAITEN_TAG_PRINT_ID: int = 997546  # Тег "распечатать"

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
