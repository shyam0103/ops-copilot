from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.base import Base
from app.api.auth import router as auth_router

app = FastAPI()

# CORS (important for Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ops-copilot.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 CREATE TABLES ON STARTUP
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# Routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
def health():
    return {"status": "ok"}
