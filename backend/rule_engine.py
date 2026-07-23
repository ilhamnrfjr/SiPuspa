from database import Database

FALLBACK_TEXT = (
    "Maaf, saya tidak memahami pertanyaan Anda. 🙏\n\n"
    "Saya dapat membantu informasi seputar:\n"
    "• Jam operasional perpustakaan\n"
    "• Lokasi dan fasilitas\n"
    "• Cara peminjaman buku\n"
    "• Keanggotaan dan denda\n"
    "• Layanan digital\n"
    "• Dan informasi umum perpustakaan lainnya\n\n"
    "Silakan coba tanyakan kembali, atau hubungi petugas perpustakaan untuk bantuan lebih lanjut."
)

FALLBACK_QUICK_REPLIES = [
    "Jam Operasional",
    "Cara Pinjam Buku",
    "Lokasi Perpustakaan",
    "Kontak Perpustakaan"
]


class RuleEngine:
    def __init__(self):
        self.db = Database()

    def get_response(self, intent, entities, session_id):
        # Pertanyaan di luar konteks — langsung fallback tanpa query DB
        if intent == 'not_understood' or not intent:
            return {
                'text':          FALLBACK_TEXT,
                'quick_replies': FALLBACK_QUICK_REPLIES
            }

        row = self.db.get_intent_by_name(intent)

        # Intent ada di DB
        if row and row.get('response_text'):
            return {
                'text':          row['response_text'],
                'quick_replies': row.get('quick_replies', [])
            }

        # Intent 'lainnya' atau tidak ditemukan di DB — gunakan fallback
        return {
            'text':          FALLBACK_TEXT,
            'quick_replies': FALLBACK_QUICK_REPLIES
        }