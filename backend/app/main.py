# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat
from app.api import documents
from app.api import tickets
from app.api import auth

app = FastAPI(title="OpsCopilot Backend", version="0.1.0")

# CORS - Allow Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your Vercel URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
from app.core.db import init_db

@app.on_event("startup")
def startup_event():
    print("🚀 Initializing database...")
    init_db()
    print("✅ Database ready!")

# Routers
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "OpsCopilot API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}