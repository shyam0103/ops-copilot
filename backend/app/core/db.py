 # app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import Base

DATABASE_URL = "sqlite:///./opscopilot.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
def init_db():
    Base.metadata.create_all(bind=engine)

