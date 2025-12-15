from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.base import Base

# IMPORTANT: import models so SQLAlchemy knows them
from app.models import user  # noqa: F401

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.tickets import router as tickets_router

app = FastAPI(title="OpsCopilot API")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ops-copilot.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# STARTUP: CREATE TABLES
# -----------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# -----------------------------
# ROUTERS
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(tickets_router, prefix="/api", tags=["Tickets"])

@app.get("/")
def health():
    return {"status": "ok"}
