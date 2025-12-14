from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, documents, tickets

app = FastAPI(title="OpsCopilot API")

# ✅ EXACT origins
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ops-copilot.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],          # IMPORTANT
    allow_headers=["*"],          # 🔥 THIS FIXES YOUR ISSUE
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])

@app.get("/")
def root():
    return {"status": "OpsCopilot backend running"}
