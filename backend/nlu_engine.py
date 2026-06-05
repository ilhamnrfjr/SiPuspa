import re
import json
from rapidfuzz import fuzz
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

class NLUEngine:
    def __init__(self, intents_path='data/intents.json'):
        # Load intents
        with open(intents_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.intents = data['intents']
        
        # Initialize Indonesian stemmer
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()
        
        # Stopwords untuk bahasa Indonesia
        self.stopwords = set([
            'yang', 'untuk', 'pada', 'ke', 'para', 'namun', 'menurut', 'antara',
            'dia', 'dua', 'ia', 'seperti', 'jika', 'jika', 'sehingga', 'kembali',
            'dan', 'ini', 'itu', 'adalah', 'ada', 'dari', 'di', 'dengan', 'oleh',
            'tersebut', 'dalam', 'akan', 'dapat', 'telah', 'sudah', 'bisa', 'bisa',
            'apa', 'siapa', 'kapan', 'dimana', 'mengapa', 'bagaimana', 'berapa'
        ])
        
        # Synonym mapping untuk meningkatkan akurasi
        self.synonyms = {
            'pinjam': ['meminjam', 'peminjaman', 'minjem'],
            'buka': ['dibuka', 'operasional', 'beroperasi'],
            'lokasi': ['tempat', 'alamat', 'posisi', 'dimana', 'di mana'],
            'koleksi': ['buku', 'pustaka', 'referensi', 'katalog'],
            'ruang': ['room', 'tempat', 'area'],
            'jadwal': ['schedule', 'waktu', 'kapan'],
            'cara': ['bagaimana', 'gimana', 'prosedur', 'proses'],
            'fasilitas': ['sarana', 'prasarana', 'amenitas'],
            'booking': ['reservasi', 'pesan', 'book'],
            'acara': ['event', 'kegiatan', 'agenda'],
            'daftar': ['mendaftar', 'pendaftaran', 'register'],
            'denda': ['sanksi', 'penalty', 'fine']
        }
    
    def preprocess(self, text):
        """Preprocessing teks input"""
        # Lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text):
        """Tokenisasi sederhana"""
        return text.split()
    
    def remove_stopwords(self, tokens):
        """Hapus stopwords"""
        return [token for token in tokens if token not in self.stopwords]
    
    def stem_tokens(self, tokens):
        """Stemming menggunakan Sastrawi"""
        return [self.stemmer.stem(token) for token in tokens]
    
    def expand_synonyms(self, text):
        """Ekspansi sinonim untuk meningkatkan matching"""
        words = text.split()
        expanded = []
        
        for word in words:
            expanded.append(word)
            # Tambahkan sinonim jika ada
            for key, synonyms in self.synonyms.items():
                if word in synonyms or word == key:
                    expanded.extend([key] + synonyms)
        
        return ' '.join(expanded)
    
    def calculate_similarity(self, text1, text2):
        """Hitung similarity score antara dua teks"""
        # Token sort ratio untuk handle word order
        token_sort_score = fuzz.token_sort_ratio(text1, text2)
        
        # Partial ratio untuk handle substring matching
        partial_score = fuzz.partial_ratio(text1, text2)
        
        # Token set ratio untuk handle different word sets
        token_set_score = fuzz.token_set_ratio(text1, text2)
        
        # Weighted average
        similarity = (token_sort_score * 0.5 + partial_score * 0.2 + token_set_score * 0.3)
        
        return similarity / 100  # Normalize to 0-1
    
    def extract_intent(self, user_input):
        """Ekstraksi intent dari input pengguna"""
        # Preprocess input
        processed_input = self.preprocess(user_input)
        
        # Expand synonyms
        expanded_input = self.expand_synonyms(processed_input)
        
        # Tokenize
        tokens = self.tokenize(processed_input)
        
        # Remove stopwords
        filtered_tokens = self.remove_stopwords(tokens)

        if len(filtered_tokens) == 0:
            return {'intent': 'not_understood', 'confidence': 0.0, 'matched_pattern': None}
        
        # Stem tokens
        stemmed_tokens = self.stem_tokens(filtered_tokens)
        stemmed_text = ' '.join(stemmed_tokens)
        
        # Match dengan pattern di setiap intent
        best_match = {
            'intent': 'lainnya',
            'confidence': 0.0,
            'matched_pattern': None
        }
        
        for intent_data in self.intents:
            intent_name = intent_data['intent']
            patterns = intent_data['patterns']
            
            for pattern in patterns:
                # Preprocess pattern
                processed_pattern = self.preprocess(pattern)
                expanded_pattern = self.expand_synonyms(processed_pattern)
                
                # Calculate similarity
                similarity = self.calculate_similarity(expanded_input, expanded_pattern)
                
                # Update best match jika similarity lebih tinggi
                if similarity > best_match['confidence']:
                    best_match = {
                        'intent': intent_name,
                        'confidence': similarity,
                        'matched_pattern': pattern
                    }
        
        # Set threshold minimum confidence
        if best_match['confidence'] < 0.70:
            best_match['intent'] = 'not_understood'
            best_match['confidence'] = 0.0
        
        return best_match
    
    def extract_entities(self, user_input, intent):
        """Ekstraksi entity dari input pengguna"""
        entities = {}
        
        # Entity extraction berdasarkan intent
        if intent == 'jam_operasional':
            # Extract hari
            hari_pattern = r'\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu)\b'
            hari_match = re.search(hari_pattern, user_input.lower())
            if hari_match:
                entities['hari'] = hari_match.group(1)
            
            # Extract jam
            jam_pattern = r'\b(\d{1,2}):?(\d{2})?\s*(pagi|siang|sore|malam)?\b'
            jam_match = re.search(jam_pattern, user_input.lower())
            if jam_match:
                entities['jam'] = jam_match.group(0)
        
        elif intent == 'lokasi':
            # Extract lantai
            lantai_pattern = r'\blantai\s*(\d+|satu|dua|tiga)\b'
            lantai_match = re.search(lantai_pattern, user_input.lower())
            if lantai_match:
                entities['lantai'] = lantai_match.group(1)
            
            # Extract gedung
            gedung_pattern = r'\bgedung\s*([A-Z]|utama|timur|barat)\b'
            gedung_match = re.search(gedung_pattern, user_input.lower())
            if gedung_match:
                entities['gedung'] = gedung_match.group(1)
        
        elif intent == 'koleksi':
            # Extract judul (simplified - bisa diperbaiki dengan NER)
            if 'buku' in user_input.lower():
                # Ambil kata setelah 'buku'
                buku_pattern = r'buku\s+(["\']?[\w\s]+["\']?)'
                buku_match = re.search(buku_pattern, user_input.lower())
                if buku_match:
                    entities['judul'] = buku_match.group(1).strip('"\'')
            
            # Extract bahasa
            bahasa_pattern = r'\b(indonesia|inggris|arab|jepang)\b'
            bahasa_match = re.search(bahasa_pattern, user_input.lower())
            if bahasa_match:
                entities['bahasa'] = bahasa_match.group(1)
        
        elif intent == 'study_buddy':
            # Extract tanggal
            tanggal_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
            tanggal_match = re.search(tanggal_pattern, user_input)
            if tanggal_match:
                entities['tanggal'] = tanggal_match.group(1)
            
            # Extract jam
            jam_pattern = r'\b(\d{1,2}):?(\d{2})\b'
            jam_match = re.search(jam_pattern, user_input)
            if jam_match:
                entities['jam'] = jam_match.group(0)
            
            # Extract jumlah orang
            orang_pattern = r'\b(\d+)\s*orang\b'
            orang_match = re.search(orang_pattern, user_input.lower())
            if orang_match:
                entities['jumlah_orang'] = int(orang_match.group(1))
        
        return entities
    
    def process(self, user_input):
        """Main processing pipeline"""
        # Extract intent
        intent_result = self.extract_intent(user_input)
        
        # Extract entities
        entities = self.extract_entities(user_input, intent_result['intent'])
        
        return {
            'intent': intent_result['intent'],
            'confidence': intent_result['confidence'],
            'matched_pattern': intent_result['matched_pattern'],
            'entities': entities
        }