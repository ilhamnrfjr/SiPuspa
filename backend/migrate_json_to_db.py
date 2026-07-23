import json
import os
from database import Database

db = Database()

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE  = os.path.join(BASE_DIR, 'data', 'intents.json')
RESPONSES_FILE= os.path.join(BASE_DIR, 'data', 'responses.json')

# ── Load responses.json → dict {response_key: {text, quick_replies}} ──
responses = {}
if os.path.exists(RESPONSES_FILE):
    with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
        resp_data = json.load(f)
    responses = resp_data.get('responses', {})
    print(f"📄 responses.json: {len(responses)} response ditemukan")
else:
    print("⚠️  responses.json tidak ditemukan — response_text akan kosong")

# ── Migrasi intents.json ───────────────────────────────────────────────
if not os.path.exists(INTENTS_FILE):
    print("❌ intents.json tidak ditemukan, hentikan migrasi.")
    exit(1)

with open(INTENTS_FILE, 'r', encoding='utf-8') as f:
    intent_data = json.load(f)

intents = intent_data.get('intents', [])
print(f"📄 intents.json: {len(intents)} intent ditemukan\n")

sukses = 0
gagal  = 0

for intent in intents:
    intent_name  = intent.get('intent', '')
    patterns     = intent.get('patterns', [])
    response_key = intent.get('response_key', '')

    # Ambil teks jawaban dari responses.json berdasarkan response_key
    resp_obj      = responses.get(response_key, {})
    response_text = resp_obj.get('text', '')
    quick_replies = resp_obj.get('quick_replies', [])

    if not intent_name or not patterns:
        print(f"⚠️  Skip (data tidak lengkap): {intent_name}")
        gagal += 1
        continue

    try:
        db.add_intent(
            intent_name   = intent_name,
            patterns      = patterns,
            response_text = response_text,
            quick_replies = quick_replies
        )
        status = "✅" if response_text else "✅ (response kosong — isi manual di dashboard)"
        print(f"{status} {intent_name}")
        sukses += 1
    except Exception as e:
        print(f"⚠️  {intent_name}: {e}")
        gagal += 1

print(f"\n{'='*50}")
print(f"Migrasi selesai: {sukses} berhasil, {gagal} gagal/skip")
if gagal == 0:
    print("✅ Semua intent berhasil dipindahkan ke MySQL!")
    print("💡 Sekarang kamu bisa mengedit response langsung dari tab 'Manage Intents' di dashboard.")
else:
    print("⚠️  Ada beberapa intent yang perlu ditambahkan manual via dashboard.")