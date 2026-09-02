from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LUIP API"
    APP_VERSION: str = "1.3.5"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # =====================================================
    # DEFAULT / LEGACY SMTP
    # =====================================================
    #
    # These settings remain supported for backwards
    # compatibility.
    #
    # Provider:
    #
    #     default
    #
    # uses these settings.
    #

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Lawyered Up"

    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    SMTP_TIMEOUT: int = 30

    # =====================================================
    # GMAIL SMTP
    # =====================================================

    GMAIL_SMTP_HOST: str = "smtp.gmail.com"
    GMAIL_SMTP_PORT: int = 587

    GMAIL_SMTP_USERNAME: str = ""
    GMAIL_SMTP_PASSWORD: str = ""

    GMAIL_SMTP_FROM_EMAIL: str = ""
    GMAIL_SMTP_FROM_NAME: str = "Lawyered Up"

    GMAIL_SMTP_USE_TLS: bool = True
    GMAIL_SMTP_USE_SSL: bool = False

    GMAIL_SMTP_TIMEOUT: int = 30

    # =====================================================
    # OUTLOOK / MICROSOFT SMTP
    # =====================================================

    OUTLOOK_SMTP_HOST: str = "smtp.office365.com"
    OUTLOOK_SMTP_PORT: int = 587

    OUTLOOK_SMTP_USERNAME: str = ""
    OUTLOOK_SMTP_PASSWORD: str = ""

    OUTLOOK_SMTP_FROM_EMAIL: str = ""
    OUTLOOK_SMTP_FROM_NAME: str = "Lawyered Up"

    OUTLOOK_SMTP_USE_TLS: bool = True
    OUTLOOK_SMTP_USE_SSL: bool = False

    OUTLOOK_SMTP_TIMEOUT: int = 30

    # =====================================================
    # ZOHO SMTP
    # =====================================================

    ZOHO_SMTP_HOST: str = "smtp.zoho.com"
    ZOHO_SMTP_PORT: int = 587

    ZOHO_SMTP_USERNAME: str = ""
    ZOHO_SMTP_PASSWORD: str = ""

    ZOHO_SMTP_FROM_EMAIL: str = ""
    ZOHO_SMTP_FROM_NAME: str = "Lawyered Up"

    ZOHO_SMTP_USE_TLS: bool = True
    ZOHO_SMTP_USE_SSL: bool = False

    ZOHO_SMTP_TIMEOUT: int = 30

    # =====================================================
    # SMTP PROVIDER ROUTING
    # =====================================================
    #
    # Supported values:
    #
    #     default
    #     gmail
    #     outlook
    #     zoho
    #
    # Existing EmailQueue records use "default" unless
    # explicitly assigned another provider.
    #

    SMTP_DEFAULT_PROVIDER: str = "default"

    # =====================================================
    # EMAIL SAFETY
    # =====================================================
    #
    # True:
    #     Emails are prepared but NOT transmitted.
    #
    # False:
    #     Live SMTP transmission may be used, subject to
    #     EMAIL_LIVE_ENABLED.
    #

    EMAIL_DRY_RUN: bool = True

    # Explicit operator authorization for live email.
    #
    # Live transmission requires BOTH:
    #
    #     EMAIL_DRY_RUN=False
    #     EMAIL_LIVE_ENABLED=True
    #

    EMAIL_LIVE_ENABLED: bool = False

    # =====================================================
    # EMAIL BATCH LIMITS
    # =====================================================

    EMAIL_BATCH_SIZE: int = 10

    EMAIL_LIVE_MAX_BATCH: int = 1

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

DATABASE_URL = settings.DATABASE_URL