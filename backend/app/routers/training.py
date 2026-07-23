import json
from sqlalchemy import text

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.deps import get_current_user
from app.nlu.engine import NLUEngine
from app.schemas import TrainingTestRequest

router = APIRouter(prefix="/api/training", tags=["Training"])


@router.post("/test")
def test_message(
    req: TrainingTestRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    nlu = NLUEngine(db)
    result = nlu.process(req.message)

    response_text = None
    quick_replies = []
    if result["intent"] != "not_understood":
        row = db.execute(
            text("SELECT response_text, quick_replies FROM intents WHERE intent_name = :name"),
            {"name": result["intent"]},
        ).first()
        if row:
            response_text = row[0]
            if row[1]:
                try:
                    quick_replies = json.loads(row[1])
                except (json.JSONDecodeError, TypeError):
                    quick_replies = []

    return {
        "intent": result["intent"],
        "confidence": round(result["confidence"], 2),
        "entities": result["entities"],
        "matched_pattern": result["matched_pattern"],
        "response_preview": response_text,
        "quick_replies": quick_replies if isinstance(quick_replies, list) else [],
    }


@router.get("/history")
def get_training_history(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return {"history": []}
