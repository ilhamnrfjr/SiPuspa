# PUSPA — Chatbot Perpustakaan BPK RI

Sistem chatbot **rule-based** untuk otomasi layanan informasi Perpustakaan BPK RI. Dibangun dengan **FastAPI** + **React** + **MySQL**.

## Tech Stack

| Layer     | Teknologi                              |
|-----------|----------------------------------------|
| Backend   | Python 3.11+ · FastAPI · SQLAlchemy    |
| Database  | MySQL (InnoDB)                         |
| NLU       | Fuzzy matching + Rapidfuzz · Sastrawi  |
| Auth      | JWT + bcrypt                           |
| Frontend  | React 18 · Vite · Tailwind CSS         |
| Charts    | Recharts                                |
| Icons     | Lucide React                           |

## Struktur Proyek

```
chatbot-bpk/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          ← FastAPI app & router registration
│   │   ├── config.py        ← Konfigurasi (.env)
│   │   ├── database.py      ← SQLAlchemy engine & session
│   │   ├── models.py        ← Model database (ORM)
│   │   ├── schemas.py       ← Pydantic schemas
│   │   ├── auth.py          ← JWT + bcrypt auth
│   │   ├── nlu/
│   │   │   └── engine.py    ← NLU Engine (fuzzy + entity extraction)
│   │   └── routers/
│   │       ├── auth.py      ← /api/auth/*
│   │       ├── chat.py      ← /api/chat/*
│   │       ├── intents.py   ← /api/intents/*
│   │       ├── analytics.py ← /api/analytics/*
│   │       ├── users.py     ← /api/users/*
│   │       └── training.py  ← /api/training/*
│   ├── data/
│   │   ├── intents.json     ← Data intent & pola
│   │   ├── responses.json   ← Template respons
│   │   └── sipuspa_data.json
│   ├── seed_data.py         ← Isi database awal
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx          ← Router utama
│   │   ├── api/client.js    ← API client + JWT interceptor
│   │   ├── context/AuthContext.jsx
│   │   ├── components/
│   │   │   ├── Layout.jsx   ← Wrapper dengan sidebar
│   │   │   └── Sidebar.jsx  ← Navigasi admin
│   │   └── pages/
│   │       ├── ChatDemo.jsx ← Chat publik
│   │       ├── Login.jsx    ← Login admin
│   │       ├── Dashboard.jsx← Overview statistik
│   │       ├── Analytics.jsx← Grafik & analitik
│   │       ├── ChatLogs.jsx ← Log percakapan
│   │       ├── Intents.jsx  ← Kelola intent
│   │       ├── Training.jsx ← Uji NLU
│   │       └── Users.jsx    ← Kelola akun
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md
```

## Instalasi

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Dokumentasi API: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Buka: http://localhost:5173

## Akun Login

| Username      | Password        | Role        |
|---------------|-----------------|-------------|
| `superadmin`  | `Admin@BPK2025` | Superadmin  |
| `admin_puspa` | `Puspa@2025`    | Admin       |

## API Endpoints

| Method | Path                    | Deskripsi              | Auth |
|--------|-------------------------|------------------------|------|
| POST   | /api/auth/login         | Login admin            | No   |
| GET    | /api/auth/me            | Info user              | Yes  |
| POST   | /api/chat/message       | Kirim pesan chatbot    | No   |
| POST   | /api/chat/feedback/{id} | Submit feedback        | No   |
| GET    | /api/intents/           | List intent            | Yes  |
| POST   | /api/intents/           | Tambah intent          | Yes  |
| PUT    | /api/intents/{name}     | Update intent          | Yes  |
| DELETE | /api/intents/{name}     | Hapus intent           | Yes  |
| GET    | /api/analytics/summary  | Statistik              | Yes  |
| GET    | /api/analytics/logs     | Log percakapan         | Yes  |
| DELETE | /api/analytics/logs     | Hapus semua log        | Yes  |
| GET    | /api/users/             | List user              | Yes  |
| POST   | /api/users/             | Tambah user (super)    | Super |
| POST   | /api/training/test      | Uji pesan NLU          | Yes  |
