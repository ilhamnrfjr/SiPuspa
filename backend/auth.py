import mysql.connector
import hashlib
import secrets
from datetime import datetime, timedelta
from database import DB_CONFIG


class AuthSystem:
    def __init__(self):
        self.config = DB_CONFIG
        self.init_auth_tables()
        self.create_default_superadmin()

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def init_auth_tables(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                username   VARCHAR(80)  NOT NULL UNIQUE,
                password   VARCHAR(255) NOT NULL,
                full_name  VARCHAR(150),
                role       ENUM('superadmin','admin') NOT NULL DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                user_id    INT NOT NULL,
                token      VARCHAR(100) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        conn.commit(); cur.close(); conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_default_superadmin(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM admin_users')
        if cur.fetchone()[0] == 0:
            cur.execute(
                'INSERT INTO admin_users (username,password,full_name,role) VALUES (%s,%s,%s,%s)',
                ('admin', self.hash_password('admin123'), 'Super Administrator', 'superadmin')
            )
            conn.commit()
            print("Default superadmin dibuat: admin / admin123")
        cur.close(); conn.close()

    def login(self, username, password):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute(
            'SELECT id,username,full_name,role FROM admin_users WHERE username=%s AND password=%s',
            (username, self.hash_password(password))
        )
        user = cur.fetchone()
        if not user:
            cur.close(); conn.close()
            return {'success': False, 'message': 'Username atau password salah'}
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        cur.execute('INSERT INTO admin_sessions (user_id,token,expires_at) VALUES (%s,%s,%s)',
                    (user['id'], token, expires_at))
        cur.execute('UPDATE admin_users SET last_login=NOW() WHERE id=%s', (user['id'],))
        conn.commit(); cur.close(); conn.close()
        return {
            'success': True, 'token': token,
            'user': {'id': user['id'], 'username': user['username'],
                     'full_name': user['full_name'], 'role': user['role']}
        }

    def verify_token(self, token):
        if not token: return None
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT u.id,u.username,u.full_name,u.role,s.expires_at
            FROM admin_sessions s JOIN admin_users u ON s.user_id=u.id
            WHERE s.token=%s
        ''', (token,))
        row = cur.fetchone(); cur.close(); conn.close()
        if row and row['expires_at'] > datetime.now():
            return {'id': row['id'], 'username': row['username'],
                    'full_name': row['full_name'], 'role': row['role']}
        return None

    def logout(self, token):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('DELETE FROM admin_sessions WHERE token=%s', (token,))
        conn.commit(); cur.close(); conn.close()

    def change_password(self, user_id, old_password, new_password):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('SELECT id FROM admin_users WHERE id=%s AND password=%s',
                    (user_id, self.hash_password(old_password)))
        if cur.fetchone():
            cur.execute('UPDATE admin_users SET password=%s WHERE id=%s',
                        (self.hash_password(new_password), user_id))
            conn.commit(); cur.close(); conn.close()
            return {'success': True, 'message': 'Password berhasil diubah'}
        cur.close(); conn.close()
        return {'success': False, 'message': 'Password lama salah'}

    def get_all_users(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id,username,full_name,role,created_at,last_login FROM admin_users ORDER BY id')
        rows = cur.fetchall(); cur.close(); conn.close()
        for r in rows:
            for k in ('created_at','last_login'):
                if isinstance(r[k], datetime): r[k] = r[k].strftime('%Y-%m-%d %H:%M:%S')
        return rows

    def add_user(self, username, password, full_name, role='admin'):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('INSERT INTO admin_users (username,password,full_name,role) VALUES (%s,%s,%s,%s)',
                    (username, self.hash_password(password), full_name, role))
        conn.commit(); new_id = cur.lastrowid; cur.close(); conn.close()
        return new_id

    def update_user(self, user_id, full_name, role):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('UPDATE admin_users SET full_name=%s,role=%s WHERE id=%s', (full_name, role, user_id))
        conn.commit(); cur.close(); conn.close()

    def delete_user(self, user_id):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('DELETE FROM admin_users WHERE id=%s', (user_id,))
        conn.commit(); cur.close(); conn.close()