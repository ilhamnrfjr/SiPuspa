import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

class AuthSystem:
    def __init__(self, db_name='chatbot.db'):
        self.db_name = db_name
        self.init_auth_tables()
        self.create_default_admin()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_auth_tables(self):
        """Inisialisasi tabel untuk autentikasi"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabel users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Tabel sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admin_users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password dengan SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_admin(self):
        """Buat admin default jika belum ada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM admin_users')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Default admin: username=admin, password=admin123
            password_hash = self.hash_password('admin123')
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, full_name, email)
                VALUES (?, ?, ?, ?)
            ''', ('admin', password_hash, 'Administrator', 'admin@perpustakaan.bpk.go.id'))
            conn.commit()
            print("✅ Default admin created - Username: admin, Password: admin123")
        
        conn.close()
    
    def login(self, username, password):
        """Login dan generate token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute('''
            SELECT id, username, full_name, email 
            FROM admin_users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
            
            # Generate token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            # Simpan session
            cursor.execute('''
                INSERT INTO admin_sessions (user_id, token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, token, expires_at))
            
            # Update last login
            cursor.execute('''
                UPDATE admin_users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[2],
                    'email': user[3]
                }
            }
        else:
            conn.close()
            return {
                'success': False,
                'message': 'Username atau password salah'
            }
    
    def verify_token(self, token):
        """Verifikasi token session"""
        if not token:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.full_name, u.email, s.expires_at
            FROM admin_sessions s
            JOIN admin_users u ON s.user_id = u.id
            WHERE s.token = ?
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            expires_at = datetime.fromisoformat(result[4])
            if expires_at > datetime.now():
                return {
                    'id': result[0],
                    'username': result[1],
                    'full_name': result[2],
                    'email': result[3]
                }
        
        return None
    
    def logout(self, token):
        """Logout - hapus session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM admin_sessions WHERE token = ?', (token,))
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def change_password(self, user_id, old_password, new_password):
        """Ubah password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        old_hash = self.hash_password(old_password)
        
        cursor.execute('''
            SELECT id FROM admin_users 
            WHERE id = ? AND password_hash = ?
        ''', (user_id, old_hash))
        
        if cursor.fetchone():
            new_hash = self.hash_password(new_password)
            cursor.execute('''
                UPDATE admin_users SET password_hash = ?
                WHERE id = ?
            ''', (new_hash, user_id))
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Password berhasil diubah'}
        else:
            conn.close()
            return {'success': False, 'message': 'Password lama salah'}