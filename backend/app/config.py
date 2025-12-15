# app/config.py
import os

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    DATABASE_URL: str = "sqlite:///./opscopilot.db"

settings = Settings()