from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRATION: int
    JWT_REFRESH_EXPIRATION: int
    REFRESH_TOKEN_EXPIRY_DAYS: int
    PASSWORD_EXPIRY_DAYS: int
    ACCOUNT_LOCK_MAX_COUNT: int
    OTP_RESEND_MAX_COUNT: int
    OTP_SEND_MAX_HOURS: int
    OTP_EXPIRY_MINUTES: int
    MAX_NUMBER_OF_REQUESTS: int
    OPENAI_API_KEY: str
    SENTIMENT_ANALYSIS: str

    class Config:
        env_file = ".env"

settings = Settings()
