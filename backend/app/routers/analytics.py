import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import get_db
from app.models import ConversationLog
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    total_sessions = db.query(ConversationLog.session_id).distinct().count()
    total_messages = db.query(ConversationLog).count()
    avg_rt = db.query(func.avg(ConversationLog.response_time)).scalar() or 0
    avg_conf = db.query(func.avg(ConversationLog.confidence)).scalar() or 0

    top_intents = (
        db.query(
            ConversationLog.intent_detected.label("intent"),
            func.count().label("count"),
        )
        .filter(ConversationLog.intent_detected.isnot(None))
        .group_by(ConversationLog.intent_detected)
        .order_by(func.count().desc())
        .all()
    )

    messages_per_day = (
        db.query(
            func.date(ConversationLog.timestamp).label("date"),
            func.count().label("count"),
        )
        .filter(ConversationLog.timestamp >= text("DATE_SUB(NOW(), INTERVAL 7 DAY)"))
        .group_by(func.date(ConversationLog.timestamp))
        .order_by("date")
        .all()
    )

    return {
        "total_conversations": total_sessions,
        "total_messages": total_messages,
        "avg_response_time": round(float(avg_rt), 3),
        "avg_confidence": round(float(avg_conf), 2),
        "top_intents": [
            {"intent": r.intent, "count": r.count} for r in top_intents
        ],
        "messages_per_day": [
            {"date": str(r.date), "count": r.count} for r in messages_per_day
        ],
    }


@router.get("/hourly")
def get_hourly(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = (
        db.query(
            func.hour(ConversationLog.timestamp).label("hour"),
            func.count().label("count"),
        )
        .filter(ConversationLog.timestamp >= text("DATE_SUB(NOW(), INTERVAL 7 DAY)"))
        .group_by(func.hour(ConversationLog.timestamp))
        .order_by("hour")
        .all()
    )
    hmap = {r.hour: r.count for r in rows}
    hourly = [{"hour": h, "count": hmap.get(h, 0)} for h in range(24)]
    return {"hourly": hourly}


@router.get("/confidence")
def get_confidence_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rows = (
        db.query(
            ConversationLog.intent_detected.label("intent"),
            func.avg(ConversationLog.confidence).label("avg_confidence"),
            func.count().label("count"),
        )
        .filter(
            ConversationLog.intent_detected.isnot(None),
            ConversationLog.confidence.isnot(None),
        )
        .group_by(ConversationLog.intent_detected)
        .order_by(func.avg(ConversationLog.confidence).asc())
        .all()
    )
    return {
        "confidence_stats": [
            {
                "intent": r.intent,
                "avg_confidence": round(float(r.avg_confidence), 3),
                "count": r.count,
            }
            for r in rows
        ]
    }


@router.get("/logs")
def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    intent: str = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(ConversationLog)
    if search:
        q = q.filter(
            ConversationLog.user_message.like(f"%{search}%")
            | ConversationLog.bot_response.like(f"%{search}%")
        )
    if intent:
        q = q.filter(ConversationLog.intent_detected == intent)
    total = q.count()
    rows = q.order_by(ConversationLog.timestamp.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "user_message": r.user_message,
                "bot_response": r.bot_response,
                "intent": r.intent_detected,
                "confidence": r.confidence,
                "response_time": r.response_time,
                "feedback": r.feedback,
                "timestamp": str(r.timestamp) if r.timestamp else None,
            }
            for r in rows
        ],
    }


@router.delete("/logs/{log_id}")
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    log = db.query(ConversationLog).filter(ConversationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log tidak ditemukan")
    db.delete(log)
    db.commit()
    return {"success": True}


@router.delete("/logs")
def delete_all_logs(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    deleted = db.query(ConversationLog).delete()
    db.commit()
    return {"success": True, "deleted": deleted}


@router.get("/logs/export")
def export_logs_csv(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rows = (
        db.query(ConversationLog)
        .order_by(ConversationLog.timestamp.asc())
        .all()
    )
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writerow([
        "No", "Session ID", "Waktu", "Pesan Pengguna", "Respons Bot",
        "Intent Terdeteksi", "Confidence", "Response Time (s)", "Feedback",
    ])
    for idx, r in enumerate(rows, 1):
        writer.writerow([
            idx,
            r.session_id,
            str(r.timestamp) if r.timestamp else "",
            r.user_message,
            r.bot_response,
            r.intent_detected or "",
            f"{round((r.confidence or 0) * 100, 1)}%",
            f"{round(r.response_time or 0, 3)}",
            r.feedback or "",
        ])
    fname = f"backup_percakapan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )
