# PUSPA — Chatbot Perpustakaan BPK RI
### Panduan Instalasi & Penggunaan Lengkap

---

## Deskripsi Sistem

PUSPA adalah sistem chatbot *rule-based* dengan pendekatan *Natural Language Understanding (NLU)* untuk otomasi layanan informasi Perpustakaan BPK RI. Sistem ini memiliki:

- **Chatbot NLU Engine** — Klasifikasi intent berbasis regex, keyword matching, dan fuzzy similarity
- **11 Intent** — jam operasional, lokasi, peminjaman, koleksi, digital, keanggotaan, study buddy, usulan buku, acara, akreditasi, lainnya
- **Admin Dashboard** — Analitik, log percakapan, kelola intent/pola/respons, pelatihan NLU, kelola akun
- **REST API** — FastAPI dengan dokumentasi otomatis (Swagger UI)

---

## Tech Stack

| Layer     | Teknologi                                  |
|-----------|--------------------------------------------|
| Backend   | Python 3.11 + FastAPI + SQLAlchemy         |
| Database  | SQLite (mudah dipindah ke PostgreSQL)      |
| NLU       | Custom rule-based + rapidfuzz              |
| Auth      | JWT + bcrypt                               |
| Frontend  | React 18 + Vite + Tailwind CSS             |
| Charts    | Recharts                                   |
| Icons     | Lucide React                               |

---

## Struktur Proyek

```
chatbot-bpk/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          ← FastAPI app & router registration
│   │   ├── config.py        ← Konfigurasi (SECRET_KEY, DB URL, dsb.)
│   │   ├── database.py      ← SQLAlchemy engine & session
│   │   ├── models.py        ← Model database (User, Intent, Pattern, dll.)
│   │   ├── schemas.py       ← Pydantic schemas untuk API
│   │   ├── auth.py          ← JWT auth, bcrypt, get_current_user
│   │   ├── nlu/
│   │   │   ├── __init__.py
│   │   │   └── engine.py    ← NLU Engine (klasifikasi + entity extraction)
│   │   └── routers/
│   │       ├── auth.py      ← /api/auth/login, /me
│   │       ├── chat.py      ← /api/chat/message, /feedback
│   │       ├── intents.py   ← /api/intents, /patterns, /responses (CRUD)
│   │       ├── analytics.py ← /api/analytics/summary, /logs
│   │       └── users.py     ← /api/users, /training
│   ├── seed_data.py         ← Isi database awal (jalankan 1x)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx          ← Router utama
    │   ├── api/client.js    ← Axios instance + interceptor JWT
    │   ├── context/AuthContext.jsx
    │   ├── components/
    │   │   ├── Layout.jsx   ← Wrapper dengan sidebar
    │   │   └── Sidebar.jsx  ← Navigasi admin
    │   └── pages/
    │       ├── Login.jsx    ← Halaman login admin
    │       ├── Dashboard.jsx← Overview statistik
    │       ├── Analytics.jsx← Grafik & analitik lengkap
    │       ├── ChatLogs.jsx ← Log percakapan + filter
    │       ├── Intents.jsx  ← Kelola intent, pola, respons
    │       ├── Training.jsx ← Pelatihan & uji NLU
    │       ├── Users.jsx    ← Kelola akun admin
    │       └── ChatDemo.jsx ← Demo chat publik
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## LANGKAH INSTALASI

### Prasyarat

- **Python 3.10+** — https://python.org/downloads
- **Node.js 18+** — https://nodejs.org
- **Git** (opsional)

---

### 1. Setup Backend

```bash
# Masuk ke folder backend
cd chatbot-bpk/backend

# Buat virtual environment Python
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install semua library Python
pip install -r requirements.txt

# Isi database dengan data awal (WAJIB dijalankan 1x)
python seed_data.py

# Jalankan server backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Setelah berhasil, buka: http://localhost:8000  
Dokumentasi API: http://localhost:8000/docs

---

### 2. Setup Frontend

Buka **terminal baru** (biarkan backend tetap berjalan):

```bash
# Masuk ke folder frontend
cd chatbot-bpk/frontend

# Install semua package Node.js
npm install

# Jalankan development server
npm run dev
```

Setelah berhasil, buka: http://localhost:5173

---

### 3. Akun Login Awal

Setelah `python seed_data.py` berhasil:

| Username      | Password        | Role        |
|---------------|-----------------|-------------|
| `superadmin`  | `Admin@BPK2025` | Superadmin  |
| `admin_puspa` | `Puspa@2025`    | Admin       |
| `petugas1`    | `Petugas@2025`  | Admin       |

---

## FITUR LENGKAP

### Dashboard Utama (`/dashboard`)
- Total percakapan 30 hari terakhir
- Tingkat pemahaman chatbot (%)
- Rata-rata waktu respons (ms)
- Grafik tren harian
- Top intent teratas
- Distribusi chat per jam

### Analitik (`/analytics`)
- Filter berdasarkan periode (7/30/90/365 hari)
- Line chart tren harian
- Bar chart distribusi intent (horizontal)
- Bar chart distribusi per jam
- Pie chart distribusi feedback

### Log Percakapan (`/logs`)
- Semua riwayat chat dengan filter:
  - Cari teks pesan
  - Filter per intent
  - Filter dipahami/tidak dipahami
- Kolom: waktu, pesan, intent, confidence, waktu respons, status, feedback
- Pagination 20 per halaman
- Hapus log individual

### Kelola Intent (`/intents`)
- Daftar semua intent dengan expand/collapse
- **CRUD Intent** — tambah, edit, hapus
- **CRUD Pola** — keyword, regex, fuzzy dengan bobot
- **CRUD Respons** — template respons dengan variabel dinamis
- Variabel respons otomatis dari konfigurasi perpustakaan (contoh: `{jam_buka_senin_jumat}`)

### Pelatihan NLU (`/training`)
- Jalankan training evaluasi akurasi
- Uji pesan: ketik pesan dan lihat intent + confidence + entitas + preview respons
- Riwayat training dengan perbandingan akurasi sebelum/sesudah

### Kelola Akun (`/users`) — *Khusus Superadmin*
- Tambah, edit, hapus akun admin
- Atur role (admin / superadmin)
- Nonaktifkan akun tanpa menghapus
- Ganti password

### Demo Chat (`/chat`)
- Antarmuka chat publik untuk pengguna perpustakaan
- Saran pertanyaan populer
- Feedback 👍 / 👎 per respons
- Tampilkan intent + confidence

---

## CARA KERJA NLU ENGINE

NLU Engine terletak di `backend/app/nlu/engine.py`. Alur klasifikasi:

```
Input Pengguna
      ↓
[1] Preprocessing
    - Lowercase & normalisasi unicode
    - Ekspansi sinonim ("puspa" → "perpustakaan", "gimana" → "bagaimana")
    - Hapus tanda baca
      ↓
[2] Regex Pattern Matching (bobot tertinggi)
    - Pola regex dari database dicocokkan
    - Contoh: r"\b(jam|buka|tutup)\b" → intent jam_operasional
      ↓
[3] Keyword Scoring
    - Kata kunci dari database dicocokkan
    - Mendukung multi-keyword: "jam buka, jam tutup, operasional"
    - Skor dikalikan bobot pola
      ↓
[4] Fuzzy Matching (fallback)
    - Menggunakan rapidfuzz.fuzz.partial_ratio
    - Threshold similarity > 65%
      ↓
[5] Pilih Intent Terbaik
    - Skor tertinggi di atas threshold 0.20 → intent terklasifikasi
    - Di bawah threshold → fallback intent "lainnya"
      ↓
[6] Entity Extraction
    - Ekstrak: hari, tanggal, bulan, jumlah orang, bahasa, kategori buku
      ↓
Output: (intent_name, confidence_score, entities_dict)
```

---

## MENAMBAH/MEMODIFIKASI DATA

### Menambah Pola Baru via Dashboard
1. Login ke `/dashboard`
2. Buka menu **Kelola Intent**
3. Klik intent yang ingin ditambah pola
4. Klik **Tambah Pola**
5. Pilih tipe: `keyword`, `regex`, atau `fuzzy`
6. Isi teks pola dan bobot
7. Simpan, lalu **Latih Chatbot** di menu Training

### Mengubah Variabel Perpustakaan
Variabel seperti jam buka, alamat, dll disimpan di tabel `library_config`.  
Untuk mengubah: edit langsung di file `seed_data.py` atau melalui SQLite browser.

---

## INTEGRASI DENGAN SIPUSPA

Saat ini sistem menggunakan database lokal sebagai pengganti API SiPuspa.  
Untuk integrasi nyata, edit file `backend/app/routers/chat.py`:

```python
# Ganti bagian ini:
books = db.query(models.LibraryBook)...

# Dengan:
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://library.bpk.go.id/api/books",
        headers={"Authorization": f"Bearer {SIPUSPA_API_KEY}"},
        params={"kategori": entities.get("kategori_buku")}
    )
    books = response.json()
```

---

## BUILD PRODUCTION

### Backend (dengan Gunicorn)
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Static Files)
```bash
cd frontend
npm run build
# Output ada di folder dist/
# Deploy ke Nginx, Vercel, atau server static lainnya
```

### Nginx Config (contoh)
```nginx
server {
    listen 80;
    server_name chatbot.bpk.go.id;

    location / {
        root /var/www/chatbot-bpk/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

---

## API ENDPOINTS

| Method | Path                          | Deskripsi                    | Auth |
|--------|-------------------------------|------------------------------|------|
| POST   | /api/auth/login               | Login admin                  | No   |
| GET    | /api/auth/me                  | Info user saat ini           | Yes  |
| POST   | /api/chat/message             | Kirim pesan ke chatbot       | No   |
| POST   | /api/chat/feedback/{id}       | Submit feedback              | No   |
| GET    | /api/intents/                 | List semua intent            | Yes  |
| POST   | /api/intents/                 | Buat intent baru             | Yes  |
| PUT    | /api/intents/{id}             | Update intent                | Yes  |
| DELETE | /api/intents/{id}             | Hapus intent                 | Yes  |
| GET    | /api/patterns/                | List pola (filter per intent)| Yes  |
| POST   | /api/patterns/                | Buat pola baru               | Yes  |
| GET    | /api/responses/               | List respons                 | Yes  |
| POST   | /api/responses/               | Buat respons baru            | Yes  |
| GET    | /api/analytics/summary        | Statistik & analitik         | Yes  |
| GET    | /api/analytics/logs           | Log percakapan               | Yes  |
| DELETE | /api/analytics/logs/{id}      | Hapus log                    | Yes  |
| GET    | /api/users/                   | List pengguna admin          | Yes  |
| POST   | /api/users/                   | Tambah admin (superadmin)    | Super|
| POST   | /api/training/run             | Jalankan training            | Yes  |
| POST   | /api/training/test            | Uji pesan                    | Yes  |
| GET    | /api/training/history         | Riwayat training             | Yes  |

---

## FAQ TROUBLESHOOTING

**Q: Error "Module not found" saat jalankan backend**  
A: Pastikan virtual environment aktif dan sudah `pip install -r requirements.txt`

**Q: Frontend tidak bisa connect ke backend**  
A: Pastikan backend berjalan di port 8000. Cek `vite.config.js` proxy settings.

**Q: Login gagal padahal sudah seed data**  
A: Pastikan `python seed_data.py` berhasil dijalankan. Cek file `chatbot_bpk.db` ada di folder backend.

**Q: Chatbot tidak mengenali pertanyaan**  
A: Tambah pola di menu **Kelola Intent**, lalu jalankan **Training** di menu Pelatihan NLU.

**Q: Ganti ke PostgreSQL**  
A: Edit `backend/app/config.py`:  
```python
DATABASE_URL: str = "postgresql://user:password@localhost/chatbot_bpk"
```
Lalu `pip install psycopg2-binary`.

---

*© 2025 Muhammad Ilham Nurfajri — Proyek Akhir TRPL IPB University*  
*Perpustakaan BPK RI — Sistem Informasi Perpustakaan Pusat (SiPuspa)*
