import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Intent
from app.schemas import IntentCreate, IntentUpdate
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/intents", tags=["Intents"])


@router.get("/")
def list_intents(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(Intent).order_by(Intent.intent_name).all()
    result = []
    for r in rows:
        patterns = []
        qr = []
        if r.patterns:
            try:
                patterns = json.loads(r.patterns)
            except (json.JSONDecodeError, TypeError):
                patterns = []
        if r.quick_replies:
            try:
                qr = json.loads(r.quick_replies)
            except (json.JSONDecodeError, TypeError):
                qr = []
        result.append({
            "id": r.id,
            "intent_name": r.intent_name,
            "patterns": patterns,
            "response_text": r.response_text,
            "quick_replies": qr if isinstance(qr, list) else [],
            "created_at": str(r.created_at) if r.created_at else None,
            "updated_at": str(r.updated_at) if r.updated_at else None,
        })
    return {"intents": result}


@router.post("/")
def create_intent(
    req: IntentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    existing = db.query(Intent).filter(Intent.intent_name == req.intent_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Intent '{req.intent_name}' sudah ada")
    intent = Intent(
        intent_name=req.intent_name,
        patterns=json.dumps(req.patterns, ensure_ascii=False),
        response_text=req.response_text,
        quick_replies=json.dumps(req.quick_replies or [], ensure_ascii=False),
    )
    db.add(intent)
    db.commit()
    return {"success": True, "message": "Intent ditambahkan"}


@router.put("/{intent_name}")
def update_intent(
    intent_name: str,
    req: IntentUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    intent = db.query(Intent).filter(Intent.intent_name == intent_name).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent tidak ditemukan")
    intent.intent_name = req.intent_name
    intent.patterns = json.dumps(req.patterns, ensure_ascii=False)
    intent.response_text = req.response_text
    intent.quick_replies = json.dumps(req.quick_replies or [], ensure_ascii=False)
    db.commit()
    return {"success": True, "message": "Intent diupdate"}


@router.delete("/{intent_name}")
def delete_intent(
    intent_name: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    intent = db.query(Intent).filter(Intent.intent_name == intent_name).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent tidak ditemukan")
    db.delete(intent)
    db.commit()
    return {"success": True, "message": "Intent dihapus"}
