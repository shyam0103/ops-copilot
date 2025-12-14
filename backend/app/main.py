# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat as chat_router
from app.api import documents as docs_router
from app.api import tickets as tickets_router
from app.api import auth as auth_router
from app.core.db import init_db

app = FastAPI(
    title="OpsCopilot Backend",
    version="0.1.0",
)

# ✅ CORS — PRODUCTION SAFE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ops-copilot.vercel.app",
        "https://ops-copilot-backend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
init_db()

# Routers
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(chat_router.router, prefix="/api", tags=["chat"])
app.include_router(docs_router.router, prefix="/api", tags=["documents"])
app.include_router(tickets_router.router, prefix="/api", tags=["tickets"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
