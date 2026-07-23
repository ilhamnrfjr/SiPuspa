import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, FeedbackRequest
from app.models import ConversationLog, Intent
from app.routers.deps import get_current_user
from app.nlu.engine import NLUEngine

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _get_response(intent_name: str, db: Session):
    if intent_name in ("not_understood", None, ""):
        return {
            "text": (
                "Maaf, saya tidak memahami pertanyaan Anda.\n\n"
                "Saya dapat membantu informasi seputar:\n"
                "• Jam operasional perpustakaan\n"
                "• Lokasi dan fasilitas\n"
                "• Cara peminjaman buku\n"
                "• Keanggotaan dan denda\n"
                "• Layanan digital\n"
                "• Dan informasi umum perpustakaan lainnya\n\n"
                "Silakan coba tanyakan kembali."
            ),
            "quick_replies": [
                "Jam Operasional",
                "Cara Pinjam Buku",
                "Lokasi Perpustakaan",
                "Kontak Perpustakaan",
            ],
        }
    row = db.query(Intent).filter(Intent.intent_name == intent_name).first()
    if row and row.response_text:
        import json
        qr = []
        if row.quick_replies:
            try:
                qr = json.loads(row.quick_replies)
            except (json.JSONDecodeError, TypeError):
                qr = []
        return {"text": row.response_text, "quick_replies": qr if isinstance(qr, list) else []}
    return {
        "text": "Maaf, terjadi kesalahan. Silakan coba lagi.",
        "quick_replies": [],
    }


@router.post("/message", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    start = time.time()
    session_id = req.session_id or str(uuid.uuid4())

    nlu = NLUEngine(db)
    nlu_result = nlu.process(req.message)

    response = _get_response(nlu_result["intent"], db)
    rt = time.time() - start

    log = ConversationLog(
        session_id=session_id,
        user_message=req.message,
        bot_response=response["text"],
        intent_detected=nlu_result["intent"],
        confidence=nlu_result["confidence"],
        response_time=rt,
        feedback=0,
    )
    db.add(log)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        message=response["text"],
        quick_replies=response["quick_replies"],
        intent=nlu_result["intent"],
        confidence=round(nlu_result["confidence"], 2),
        response_time=round(rt, 3),
        entities=nlu_result["entities"],
    )


@router.post("/feedback/{log_id}")
def submit_feedback(log_id: int, req: FeedbackRequest, db: Session = Depends(get_db)):
    log = db.query(ConversationLog).filter(ConversationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log tidak ditemukan")
    log.feedback = req.feedback
    db.commit()
    return {"success": True}
