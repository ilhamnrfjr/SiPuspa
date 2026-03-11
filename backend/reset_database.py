"""
Script untuk Reset Database Chatbot Perpustakaan BPK RI
Jalankan dengan: python reset_database.py
"""

import os
import sqlite3
from datetime import datetime

def reset_database():
    """Reset database - hapus semua data dan buat ulang"""
    
    db_file = 'chatbot.db'
    
    print("=" * 60)
    print("RESET DATABASE CHATBOT PERPUSTAKAAN BPK RI")
    print("=" * 60)
    print()
    
    # Konfirmasi
    confirm = input("⚠️  PERINGATAN: Semua data akan dihapus!\nKetik 'RESET' untuk melanjutkan: ")
    
    if confirm != 'RESET':
        print("❌ Reset dibatalkan")
        return
    
    print()
    print("🔄 Memulai proses reset...")
    
    # Backup database lama jika ada
    if os.path.exists(db_file):
        backup_name = f'chatbot_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        try:
            os.rename(db_file, backup_name)
            print(f"✅ Backup dibuat: {backup_name}")
        except Exception as e:
            print(f"⚠️  Gagal membuat backup: {e}")
            return
    
    # Buat database baru
    print("🔨 Membuat database baru...")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Tabel conversation_logs
    cursor.execute('''
        CREATE TABLE conversation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            intent_detected TEXT,
            confidence REAL,
            response_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel faq_management
    cursor.execute('''
        CREATE TABLE faq_management (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel user_feedback
    cursor.execute('''
        CREATE TABLE user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            feedback_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES conversation_logs(id)
        )
    ''')
    
    # Tabel analytics
    cursor.execute('''
        CREATE TABLE analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_conversations INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            success_rate REAL DEFAULT 0,
            unique_users INTEGER DEFAULT 0
        )
    ''')
    
    # Tabel admin_users
    cursor.execute('''
        CREATE TABLE admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Tabel admin_sessions
    cursor.execute('''
        CREATE TABLE admin_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES admin_users(id)
        )
    ''')
    
    print("✅ Tabel berhasil dibuat")
    
    # Buat admin default
    import hashlib
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    
    cursor.execute('''
        INSERT INTO admin_users (username, password_hash, full_name, email)
        VALUES (?, ?, ?, ?)
    ''', ('admin', password_hash, 'Administrator', 'admin@perpustakaan.bpk.go.id'))
    
    print("✅ Admin default dibuat (username: admin, password: admin123)")
    
    # Insert sample data untuk testing (optional)
    print("\n📝 Menambahkan sample data...")
    
    sample_conversations = [
        ('sess_001', 'Jam buka perpustakaan', 'Response jam operasional...', 'jam_operasional', 0.95, 0.05),
        ('sess_001', 'Lokasi perpustakaan', 'Response lokasi...', 'lokasi', 0.92, 0.04),
        ('sess_002', 'Cara pinjam buku', 'Response peminjaman...', 'peminjaman_buku', 0.88, 0.06),
        ('sess_003', 'Koleksi buku apa saja', 'Response koleksi...', 'koleksi', 0.85, 0.05),
    ]
    
    for conv in sample_conversations:
        cursor.execute('''
            INSERT INTO conversation_logs 
            (session_id, user_message, bot_response, intent_detected, confidence, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', conv)
    
    print(f"✅ {len(sample_conversations)} sample percakapan ditambahkan")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ RESET DATABASE SELESAI!")
    print("=" * 60)
    print()
    print("📊 Informasi Database:")
    print(f"   - File: {db_file}")
    print(f"   - Admin: admin / admin123")
    print(f"   - Sample data: {len(sample_conversations)} conversations")
    print()
    print("🚀 Restart Flask server untuk menggunakan database baru")
    print()

def quick_reset():
    """Reset cepat tanpa konfirmasi (untuk development)"""
    db_file = 'chatbot.db'
    
    if os.path.exists(db_file):
        os.remove(db_file)
        print("✅ Database lama dihapus")
    
    # Import dan jalankan init dari database.py dan auth.py
    from database import Database
    from auth import AuthSystem
    
    db = Database()
    auth = AuthSystem()
    
    print("✅ Database baru dibuat")
    print("🔐 Admin: admin / admin123")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_reset()
    else:
        reset_database()