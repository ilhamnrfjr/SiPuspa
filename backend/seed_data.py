import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE = os.path.join(BASE_DIR, "data", "intents.json")
RESPONSES_FILE = os.path.join(BASE_DIR, "data", "responses.json")

from app.database import SessionLocal
from app.models import Intent


def seed():
    db = SessionLocal()

    responses = {}
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            responses = json.load(f).get("responses", {})

    if not os.path.exists(INTENTS_FILE):
        print("intents.json tidak ditemukan")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    sukses = 0
    for item in data.get("intents", []):
        intent_name = item.get("intent", "")
        patterns = item.get("patterns", [])
        response_key = item.get("response_key", "")
        resp_obj = responses.get(response_key, {})
        response_text = resp_obj.get("text", "")
        quick_replies = resp_obj.get("quick_replies", [])

        existing = db.query(Intent).filter(Intent.intent_name == intent_name).first()
        if existing:
            continue

        intent = Intent(
            intent_name=intent_name,
            patterns=json.dumps(patterns, ensure_ascii=False),
            response_text=response_text,
            quick_replies=json.dumps(quick_replies, ensure_ascii=False),
        )
        db.add(intent)
        sukses += 1

    db.commit()
    db.close()
    print(f"Seed selesai: {sukses} intent ditambahkan")


if __name__ == "__main__":
    seed()
