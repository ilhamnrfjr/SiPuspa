import json

class RuleEngine:
    def __init__(self, responses_path='data/responses.json', sipuspa_path='data/sipuspa_data.json'):
        # Load responses
        with open(responses_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.responses = data['responses']
        
        # Load SiPuspa data (mock)
        with open(sipuspa_path, 'r', encoding='utf-8') as f:
            self.sipuspa_data = json.load(f)
        
        # Context untuk multi-turn conversation
        self.context = {}
    
    def get_response(self, intent, entities, session_id):
        """Generate response berdasarkan intent dan entities"""
        
        # Ambil base response
        if intent in self.responses:
            response_data = self.responses[intent]
        else:
            response_data = self.responses['not_understood']
        
        # Personalisasi response berdasarkan entities dan context
        response_text = response_data['text']
        quick_replies = response_data.get('quick_replies', [])
        
        # Enhanced response dengan data SiPuspa
        enhanced_response = self.enhance_with_sipuspa(intent, entities, response_text)
        
        # Update context untuk conversation continuity
        self.update_context(session_id, intent, entities)
        
        return {
            'text': enhanced_response,
            'quick_replies': quick_replies,
            'intent': intent,
            'entities': entities
        }
    
    def enhance_with_sipuspa(self, intent, entities, base_response):
        """Enhance response dengan data dari SiPuspa"""
        
        if intent == 'koleksi':
            # Jika user mencari koleksi spesifik, tambahkan info koleksi populer
            if entities.get('judul') or entities.get('bahasa'):
                koleksi_info = self.search_koleksi(entities)
                if koleksi_info:
                    base_response += f"\n\n📚 **Hasil Pencarian:**\n{koleksi_info}"
            else:
                # Tampilkan koleksi populer
                populer = self.get_koleksi_populer()
                base_response += f"\n\n🔥 **Koleksi Populer:**\n{populer}"
        
        elif intent == 'study_buddy':
            # Tambahkan info ketersediaan ruangan
            if entities.get('tanggal'):
                availability = self.check_study_buddy_availability(entities.get('tanggal'))
                base_response += f"\n\n📊 **Ketersediaan untuk {entities.get('tanggal')}:**\n{availability}"
            else:
                # Tampilkan ketersediaan hari ini
                availability = self.check_study_buddy_availability('today')
                base_response += f"\n\n📊 **Ketersediaan Hari Ini:**\n{availability}"
        
        elif intent == 'acara':
            # Tambahkan info acara mendatang
            events = self.get_upcoming_events()
            base_response += f"\n\n{events}"
        
        return base_response
    
    def search_koleksi(self, entities):
        """Cari koleksi berdasarkan entities"""
        koleksi = self.sipuspa_data['koleksi_populer']
        results = []
        
        for item in koleksi:
            match = False
            
            # Match berdasarkan judul
            if entities.get('judul'):
                if entities['judul'].lower() in item['judul'].lower():
                    match = True
            
            # Match berdasarkan bahasa
            if entities.get('bahasa'):
                # Simplified matching (bisa diperbaiki)
                if entities['bahasa'].lower() in item['judul'].lower():
                    match = True
            
            if match:
                status_icon = "✅" if item['status'] == "Tersedia" else "❌"
                results.append(
                    f"{status_icon} **{item['judul']}**\n"
                    f"   Penulis: {item['penulis']}\n"
                    f"   Tahun: {item['tahun']} | Lokasi: {item['lokasi']}\n"
                    f"   Status: {item['status']}"
                )
        
        if results:
            return "\n\n".join(results[:3])  # Max 3 results
        else:
            return "Maaf, koleksi yang Anda cari tidak ditemukan. Coba kata kunci lain atau kunjungi katalog online di library.bpk.go.id"
    
    def get_koleksi_populer(self):
        """Ambil koleksi populer"""
        koleksi = self.sipuspa_data['koleksi_populer'][:3]
        result = []
        
        for item in koleksi:
            status_icon = "✅" if item['status'] == "Tersedia" else "❌"
            result.append(
                f"{status_icon} **{item['judul']}**\n"
                f"   {item['penulis']} ({item['tahun']})\n"
                f"   Status: {item['status']}"
            )
        
        return "\n\n".join(result)
    
    def check_study_buddy_availability(self, tanggal):
        """Cek ketersediaan study buddy"""
        rooms = self.sipuspa_data['study_buddy_availability']
        result = []
        
        for room in rooms:
            available_slots = []
            for jadwal in room['jadwal_tersedia']:
                if jadwal['status'] == 'available':
                    available_slots.append(jadwal['jam'])
            
            if available_slots:
                result.append(
                    f"🏢 **{room['ruang']}** (Kapasitas: {room['kapasitas']} orang)\n"
                    f"   Tersedia: {', '.join(available_slots)}"
                )
            else:
                result.append(
                    f"🏢 **{room['ruang']}** - Penuh"
                )
        
        return "\n\n".join(result)
    
    def get_upcoming_events(self):
        """Ambil acara mendatang"""
        events = self.sipuspa_data['upcoming_events'][:2]
        result = []
        
        for event in events:
            result.append(
                f"🎯 **{event['judul']}**\n"
                f"   📅 {event['tanggal']} | ⏰ {event['waktu']}\n"
                f"   📍 {event['lokasi']}\n"
                f"   👤 Pemateri: {event['pemateri']}\n"
                f"   👥 Kuota: {event['kuota']} peserta"
            )
        
        return "\n\n".join(result)
    
    def update_context(self, session_id, intent, entities):
        """Update conversation context"""
        if session_id not in self.context:
            self.context[session_id] = {
                'history': [],
                'last_intent': None,
                'entities': {}
            }
        
        self.context[session_id]['history'].append(intent)
        self.context[session_id]['last_intent'] = intent
        self.context[session_id]['entities'].update(entities)
        
        # Keep only last 5 interactions
        if len(self.context[session_id]['history']) > 5:
            self.context[session_id]['history'] = self.context[session_id]['history'][-5:]
    
    def get_context(self, session_id):
        """Ambil context untuk session tertentu"""
        return self.context.get(session_id, {})
    
    def apply_business_rules(self, intent, entities):
        """Terapkan business rules spesifik perpustakaan"""
        rules_triggered = []
        
        # Rule: Peminjaman buku harus punya kartu anggota
        if intent == 'peminjaman_buku':
            rules_triggered.append('require_membership')
        
        # Rule: Study buddy harus booking H-1
        if intent == 'study_buddy':
            rules_triggered.append('advance_booking_required')
        
        # Rule: Denda harus dibayar untuk bisa pinjam lagi
        if intent == 'denda':
            rules_triggered.append('payment_required')
        
        return rules_triggered