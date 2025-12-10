# app/config.py
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env file from the backend root
load_dotenv()


class Settings(BaseModel):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")


settings = Settings()
