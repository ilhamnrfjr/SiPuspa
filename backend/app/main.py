from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import engine, Base, SessionLocal
from app.routers import auth, chat, intents, analytics, users, training
from app.auth import create_default_superadmin

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    db.execute("ALTER TABLE conversation_logs ADD COLUMN feedback INT DEFAULT 0")
    db.commit()
except Exception:
    db.rollback()
create_default_superadmin(db)
db.close()

app = FastAPI(
    title="PUSPA — Chatbot Perpustakaan BPK RI",
    description="API untuk chatbot dan admin dashboard Perpustakaan BPK RI",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(intents.router)
app.include_router(analytics.router)
app.include_router(users.router)
app.include_router(training.router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Chatbot API is running", "version": "3.0.0"}


@app.get("/api")
def api_info():
    return {"message": "Chatbot Perpustakaan BPK RI API", "version": "3.0.0"}
