from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LUIP API"
    APP_VERSION: str = "1.3.4"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # =====================================================
    # SMTP / EMAIL EXECUTION
    # =====================================================

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Lawyered Up"

    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    SMTP_TIMEOUT: int = 30

    # -----------------------------------------------------
    # SAFETY
    # -----------------------------------------------------
    #
    # True  = emails are prepared but NOT transmitted.
    # False = live SMTP transmission is enabled.
    #
    # Keep this True until the pilot SMTP credentials
    # have been tested and live sending is intentionally
    # enabled.
    #

    EMAIL_DRY_RUN: bool = True

    # Maximum number of emails processed per scheduler
    # cycle.
    EMAIL_BATCH_SIZE: int = 10

    class Config:
        env_file = ".env"


settings = Settings()

DATABASE_URL = settings.DATABASE_URL