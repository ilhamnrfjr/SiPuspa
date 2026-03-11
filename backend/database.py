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
        
        # Tabel untuk log percakapan
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
        
        # Tabel untuk FAQ management
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
        
        # Tabel untuk feedback pengguna
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
        
        # Tabel untuk analytics
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
        
        # Top intents
        cursor.execute('''
            SELECT intent_detected, COUNT(*) as count
            FROM conversation_logs
            WHERE intent_detected IS NOT NULL
            GROUP BY intent_detected
            ORDER BY count DESC
            LIMIT 10
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