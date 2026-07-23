import re
from rapidfuzz import fuzz
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from database import Database

CONFIDENCE_THRESHOLD = 0.70


class NLUEngine:
    def __init__(self):
        self.db = Database()
        self.load_intents()

    def load_intents(self):
        """Load intents dari MySQL, skip intent 'lainnya' dari matching."""
        intents_raw = self.db.get_all_intents()
        self.intents = [
            {'intent': i['intent_name'], 'patterns': i['patterns']}
            for i in intents_raw
            if i['intent_name'] not in ('lainnya', 'not_understood')
        ]

        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()

        self.stopwords = set([
            'yang','untuk','pada','ke','para','namun','menurut','antara',
            'dia','dua','ia','seperti','jika','sehingga','kembali',
            'dan','ini','itu','adalah','ada','dari','di','dengan','oleh',
            'tersebut','dalam','akan','dapat','telah','sudah','bisa',
            'apa','siapa','kapan','dimana','mengapa','bagaimana','berapa'
        ])

        self.synonyms = {
            'pinjam':    ['meminjam','peminjaman','minjem'],
            'buka':      ['dibuka','operasional','beroperasi'],
            'lokasi':    ['tempat','alamat','posisi','dimana','di mana'],
            'koleksi':   ['buku','pustaka','referensi','katalog'],
            'ruang':     ['room','tempat','area'],
            'jadwal':    ['schedule','waktu','kapan'],
            'cara':      ['bagaimana','gimana','prosedur','proses'],
            'fasilitas': ['sarana','prasarana','amenitas'],
            'booking':   ['reservasi','pesan','book'],
            'acara':     ['event','kegiatan','agenda'],
            'daftar':    ['mendaftar','pendaftaran','register'],
            'denda':     ['sanksi','penalty','fine']
        }

    def preprocess(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def expand_synonyms(self, text):
        words = text.split()
        expanded = []
        for word in words:
            expanded.append(word)
            for key, synonyms in self.synonyms.items():
                if word in synonyms or word == key:
                    expanded.extend([key] + synonyms)
        return ' '.join(expanded)

    def calculate_similarity(self, text1, text2):
        s = (fuzz.token_sort_ratio(text1, text2) * 0.5 +
             fuzz.partial_ratio(text1, text2)    * 0.2 +
             fuzz.token_set_ratio(text1, text2)  * 0.3)
        return s / 100

    def extract_intent(self, user_input):
        processed = self.preprocess(user_input)
        expanded  = self.expand_synonyms(processed)
        tokens    = [t for t in processed.split() if t not in self.stopwords]

        if not tokens:
            return {'intent': 'not_understood', 'confidence': 0.0, 'matched_pattern': None}

        best = {'intent': 'not_understood', 'confidence': 0.0, 'matched_pattern': None}

        for intent_data in self.intents:
            for pattern in intent_data['patterns']:
                processed_pattern = self.preprocess(pattern)
                expanded_pattern  = self.expand_synonyms(processed_pattern)
                sim = self.calculate_similarity(expanded, expanded_pattern)
                if sim > best['confidence']:
                    best = {
                        'intent':          intent_data['intent'],
                        'confidence':      sim,
                        'matched_pattern': pattern
                    }

        # Jika confidence di bawah threshold → not_understood
        if best['confidence'] < CONFIDENCE_THRESHOLD:
            return {'intent': 'not_understood', 'confidence': 0.0, 'matched_pattern': None}

        return best

    def process(self, user_input):
        intent_result = self.extract_intent(user_input)
        return {
            'intent':          intent_result['intent'],
            'confidence':      intent_result['confidence'],
            'matched_pattern': intent_result['matched_pattern'],
            'entities':        {}
        }