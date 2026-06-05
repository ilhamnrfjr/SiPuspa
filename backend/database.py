import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='chatbot.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        """Inisialisasi database dan tabel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_logs (
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq_management (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES conversation_logs(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_conversations INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                success_rate REAL DEFAULT 0,
                unique_users INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_conversation(self, session_id, user_message, bot_response, intent, confidence, response_time):
        """Simpan log percakapan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversation_logs 
            (session_id, user_message, bot_response, intent_detected, confidence, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_message, bot_response, intent, confidence, response_time))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        return message_id
    
    def get_conversation_logs(self, limit=100, offset=0):
        """Ambil log percakapan untuk dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, user_message, bot_response, intent_detected, 
                   confidence, response_time, timestamp
            FROM conversation_logs
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': log[0],
                'session_id': log[1],
                'user_message': log[2],
                'bot_response': log[3],
                'intent': log[4],
                'confidence': log[5],
                'response_time': log[6],
                'timestamp': log[7]
            }
            for log in logs
        ]
    
    def get_analytics_summary(self):
        """Ambil summary analytics untuk dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total conversations
        cursor.execute('SELECT COUNT(DISTINCT session_id) FROM conversation_logs')
        total_conversations = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute('SELECT COUNT(*) FROM conversation_logs')
        total_messages = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute('SELECT AVG(response_time) FROM conversation_logs')
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Semua intent — tanpa LIMIT agar chart dinamis mengikuti jumlah intent aktual
        cursor.execute('''
            SELECT intent_detected, COUNT(*) as count
            FROM conversation_logs
            WHERE intent_detected IS NOT NULL
            GROUP BY intent_detected
            ORDER BY count DESC
        ''')
        top_intents = [{'intent': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Messages per day (last 7 days)
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM conversation_logs
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''')
        messages_per_day = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Average confidence
        cursor.execute('SELECT AVG(confidence) FROM conversation_logs WHERE confidence IS NOT NULL')
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'avg_response_time': round(avg_response_time, 3),
            'avg_confidence': round(avg_confidence, 2),
            'top_intents': top_intents,
            'messages_per_day': messages_per_day
        }

    def get_hourly_activity(self):
        """
        Aktivitas per jam dalam seminggu terakhir.
        Return: list of {hour: 0-23, count: N}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                   COUNT(*) as count
            FROM conversation_logs
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY hour
        ''')
        rows = cursor.fetchall()
        conn.close()

        # Pastikan semua 24 jam terisi (jam kosong = 0)
        hour_map = {row[0]: row[1] for row in rows}
        return [{'hour': h, 'count': hour_map.get(h, 0)} for h in range(24)]

    def get_intent_confidence_stats(self):
        """
        Rata-rata confidence dan jumlah kemunculan per intent.
        Berguna untuk mendeteksi intent yang perlu diperbaiki patternnya.
        Return: list of {intent, avg_confidence, count}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT intent_detected,
                   ROUND(AVG(confidence), 3) as avg_confidence,
                   COUNT(*) as count
            FROM conversation_logs
            WHERE intent_detected IS NOT NULL
              AND confidence IS NOT NULL
            GROUP BY intent_detected
            ORDER BY avg_confidence ASC
        ''')
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'intent': row[0],
                'avg_confidence': row[1],
                'count': row[2]
            }
            for row in rows
        ]

    def get_session_detail(self, session_id):
        """
        Ambil semua pesan dalam 1 session, diurutkan chronologis.
        Return: {session_id, messages: [...], summary: {total, first_time, last_time, intents}}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_message, bot_response, intent_detected,
                   confidence, response_time, timestamp
            FROM conversation_logs
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        messages = [
            {
                'id':            row[0],
                'user_message':  row[1],
                'bot_response':  row[2],
                'intent':        row[3],
                'confidence':    row[4],
                'response_time': row[5],
                'timestamp':     row[6]
            }
            for row in rows
        ]

        intents_used = list(dict.fromkeys(
            m['intent'] for m in messages if m['intent']
        ))

        return {
            'session_id': session_id,
            'messages':   messages,
            'summary': {
                'total_messages': len(messages),
                'first_time':     messages[0]['timestamp'],
                'last_time':      messages[-1]['timestamp'],
                'intents_used':   intents_used
            }
        }

    def get_sessions_list(self):
        """
        Ambil daftar session diurutkan terbaru, 1 baris per session.
        Return: list of {session_id, first_time, last_time, total_messages, intents_used}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                session_id,
                MIN(timestamp)  AS first_time,
                MAX(timestamp)  AS last_time,
                COUNT(*)        AS total_messages,
                GROUP_CONCAT(DISTINCT intent_detected) AS intents_raw
            FROM conversation_logs
            GROUP BY session_id
            ORDER BY last_time DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            intents_raw = row[4] or ''
            intents = [i.strip() for i in intents_raw.split(',') if i.strip()]
            result.append({
                'session_id':     row[0],
                'first_time':     row[1],
                'last_time':      row[2],
                'total_messages': row[3],
                'intents_used':   intents
            })
        return result

    def get_all_logs_for_backup(self):
        """Ambil semua log tanpa limit untuk keperluan backup."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, session_id, user_message, bot_response, intent_detected,
                   confidence, response_time, timestamp
            FROM conversation_logs
            ORDER BY timestamp DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id':            row[0],
                'session_id':    row[1],
                'user_message':  row[2],
                'bot_response':  row[3],
                'intent':        row[4],
                'confidence':    row[5],
                'response_time': row[6],
                'timestamp':     row[7]
            }
            for row in rows
        ]

    def delete_all_logs(self):
        """Hapus seluruh history percakapan."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conversation_logs')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_session_logs(self, session_id):
        """Hapus semua pesan dalam 1 session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM conversation_logs WHERE session_id = ?',
            (session_id,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def save_feedback(self, session_id, message_id, rating, feedback_text):
        """Simpan feedback pengguna"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback (session_id, message_id, rating, feedback_text)
            VALUES (?, ?, ?, ?)
        ''', (session_id, message_id, rating, feedback_text))
        
        conn.commit()
        conn.close()
    
    def get_faq_list(self):
        """Ambil daftar FAQ untuk management"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question, answer, category, is_active, created_at, updated_at
            FROM faq_management
            WHERE is_active = 1
            ORDER BY category, id
        ''')
        
        faqs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': faq[0],
                'question': faq[1],
                'answer': faq[2],
                'category': faq[3],
                'is_active': faq[4],
                'created_at': faq[5],
                'updated_at': faq[6]
            }
            for faq in faqs
        ]
    
    def add_faq(self, question, answer, category):
        """Tambah FAQ baru"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO faq_management (question, answer, category)
            VALUES (?, ?, ?)
        ''', (question, answer, category))
        
        conn.commit()
        faq_id = cursor.lastrowid
        conn.close()
        
        return faq_id
    
    def update_faq(self, faq_id, question, answer, category):
        """Update FAQ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE faq_management
            SET question = ?, answer = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (question, answer, category, faq_id))
        
        conn.commit()
        conn.close()
    
    def delete_faq(self, faq_id):
        """Soft delete FAQ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE faq_management
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (faq_id,))
        
        conn.commit()
        conn.close()
    
    def search_logs(self, search_query, intent_filter=None):
        """Cari dalam log percakapan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, session_id, user_message, bot_response, intent_detected, 
                   confidence, response_time, timestamp
            FROM conversation_logs
            WHERE (user_message LIKE ? OR bot_response LIKE ?)
        '''
        params = [f'%{search_query}%', f'%{search_query}%']
        
        if intent_filter:
            query += ' AND intent_detected = ?'
            params.append(intent_filter)
        
        query += ' ORDER BY timestamp DESC LIMIT 50'
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': log[0],
                'session_id': log[1],
                'user_message': log[2],
                'bot_response': log[3],
                'intent': log[4],
                'confidence': log[5],
                'response_time': log[6],
                'timestamp': log[7]
            }
            for log in logs
        ]