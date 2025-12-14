from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, documents, tickets

app = FastAPI(title="OpsCopilot API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ops-copilot.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ IMPORTANT: auth router already has prefix="/auth"
app.include_router(auth.router)

# API routes
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "OpsCopilot backend running"}
