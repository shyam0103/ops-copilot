# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat as chat_router
from app.api import documents as docs_router
from app.api import tickets as tickets_router # ⬅️ NEW
from app.api import auth as auth_router


app = FastAPI(title="OpsCopilot Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ops-copilot.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.db import init_db
init_db()

# Routers
app.include_router(chat_router.router, prefix="/api")
app.include_router(docs_router.router, prefix="/api")
app.include_router(tickets_router.router, prefix="/api") # ⬅️ NEW
app.include_router(auth_router.router)



@app.get("/health")
def health_check():
    return {"status": "ok"}