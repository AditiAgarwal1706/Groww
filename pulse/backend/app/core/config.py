from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://pulse_user:pulse_pass@localhost:5432/pulse_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change_this_secret_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # Market Data
    ALPHA_VANTAGE_API_KEY: str = ""

    # News
    NEWS_API_KEY: str = ""

    # AI
    GEMINI_API_KEY: str = ""

    # App
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

    # Workers
    MARKET_POLL_INTERVAL_SECONDS: int = 60
    NEWS_POLL_INTERVAL_SECONDS: int = 600

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except Exception:
            return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
