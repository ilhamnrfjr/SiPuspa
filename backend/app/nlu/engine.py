import re
import json

from rapidfuzz import fuzz
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from sqlalchemy.orm import Session

from app.models import Intent

CONFIDENCE_THRESHOLD = 0.70


class NLUEngine:
    def __init__(self, db: Session = None):
        self.synonyms = {
            "pinjam":    ["meminjam", "peminjaman", "minjem"],
            "buka":      ["dibuka", "operasional", "beroperasi"],
            "lokasi":    ["tempat", "alamat", "posisi", "dimana", "di mana"],
            "koleksi":   ["buku", "pustaka", "referensi", "katalog"],
            "ruang":     ["room", "tempat", "area"],
            "jadwal":    ["schedule", "waktu", "kapan"],
            "cara":      ["bagaimana", "gimana", "prosedur", "proses"],
            "fasilitas": ["sarana", "prasarana", "amenitas"],
            "booking":   ["reservasi", "pesan", "book"],
            "acara":     ["event", "kegiatan", "agenda"],
            "daftar":    ["mendaftar", "pendaftaran", "register"],
            "denda":     ["sanksi", "penalty", "fine"],
        }

        self.stopwords = {
            "yang", "untuk", "pada", "ke", "para", "namun", "menurut",
            "antara", "dia", "dua", "ia", "seperti", "jika", "sehingga",
            "kembali", "dan", "ini", "itu", "adalah", "ada", "dari", "di",
            "dengan", "oleh", "tersebut", "dalam", "akan", "dapat", "telah",
            "sudah", "bisa", "apa", "siapa", "kapan", "dimana", "mengapa",
            "bagaimana", "berapa", "saya", "aku", "anda", "kamu", "tolong",
            "mohon", "boleh", "mau", "ingin", "hendak",
        }

        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()

        self.intents = []
        if db:
            self.load_intents(db)

    def load_intents(self, db: Session):
        rows = db.query(Intent).filter(
            Intent.intent_name.notin_(["lainnya", "not_understood"])
        ).all()
        self.intents = []
        for row in rows:
            patterns = []
            if row.patterns:
                try:
                    patterns = json.loads(row.patterns)
                except (json.JSONDecodeError, TypeError):
                    patterns = []
            self.intents.append({
                "intent": row.intent_name,
                "patterns": patterns,
            })

    def preprocess(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def expand_synonyms(self, text: str) -> str:
        words = text.split()
        expanded = []
        for word in words:
            expanded.append(word)
            for key, syns in self.synonyms.items():
                if word == key or word in syns:
                    expanded.append(key)
                    expanded.extend(syns)
        return " ".join(expanded)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        s = (
            fuzz.token_sort_ratio(text1, text2) * 0.5
            + fuzz.partial_ratio(text1, text2) * 0.2
            + fuzz.token_set_ratio(text1, text2) * 0.3
        )
        return s / 100

    def extract_intent(self, user_input: str):
        processed = self.preprocess(user_input)
        expanded = self.expand_synonyms(processed)
        tokens = [t for t in processed.split() if t not in self.stopwords]

        if not tokens:
            return {"intent": "not_understood", "confidence": 0.0, "matched_pattern": None}

        best = {"intent": "not_understood", "confidence": 0.0, "matched_pattern": None}

        for intent_data in self.intents:
            for pattern in intent_data["patterns"]:
                processed_pattern = self.preprocess(pattern)
                expanded_pattern = self.expand_synonyms(processed_pattern)

                sim = self.calculate_similarity(expanded, expanded_pattern)

                if sim > best["confidence"]:
                    best = {
                        "intent": intent_data["intent"],
                        "confidence": sim,
                        "matched_pattern": pattern,
                    }

        if best["confidence"] < CONFIDENCE_THRESHOLD:
            return {"intent": "not_understood", "confidence": 0.0, "matched_pattern": None}

        return best

    def extract_entities(self, text: str) -> dict:
        entities = {}
        hari_map = {
            "senin": "Senin", "selasa": "Selasa", "rabu": "Rabu",
            "kamis": "Kamis", "jumat": "Jumat", "sabtu": "Sabtu",
            "minggu": "Minggu",
        }
        for alias, name in hari_map.items():
            if alias in text.lower():
                entities["hari"] = name
                break
        jam_match = re.search(r"(\d{1,2})[.:](\d{2})", text)
        if jam_match:
            entities["jam"] = f"{jam_match.group(1)}:{jam_match.group(2)}"
        angka_match = re.findall(r"\b(\d+)\b", text)
        if angka_match:
            nums = [int(n) for n in angka_match if int(n) < 100]
            if nums:
                entities["jumlah_orang"] = nums[0]
        return entities

    def process(self, user_input: str) -> dict:
        intent_result = self.extract_intent(user_input)
        entities = self.extract_entities(user_input)
        return {
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "matched_pattern": intent_result["matched_pattern"],
            "entities": entities,
        }
