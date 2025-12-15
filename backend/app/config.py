# backend/app/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME")
    DATABASE_URL: str = "sqlite:///./opscopilot.db"

    class Config:
        env_file = ".env"


settings = Settings()