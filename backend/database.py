import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

DB_CONFIG = {
    'host':      'localhost',
    'port':      3306,
    'user':      'root',
    'password':  '',
    'database':  'chatbot_bpk',
    'charset':   'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}


class Database:
    def __init__(self):
        self.config = DB_CONFIG
        self.init_db()

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def _fmt(self, val):
        if isinstance(val, datetime): return val.strftime('%Y-%m-%d %H:%M:%S')
        return val

    def _fmt_row(self, row, keys):
        for k in keys:
            if k in row: row[k] = self._fmt(row[k])
        return row

    def init_db(self):
        # Buat database jika belum ada
        cfg = {k: v for k, v in self.config.items() if k not in ('database','collation')}
        conn = mysql.connector.connect(**cfg); cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{self.config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit(); cur.close(); conn.close()

        conn = self.get_connection(); cur = conn.cursor()

        # ── conversation_logs ────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                session_id      VARCHAR(100) NOT NULL,
                user_message    TEXT NOT NULL,
                bot_response    TEXT NOT NULL,
                intent_detected VARCHAR(100),
                confidence      FLOAT,
                response_time   FLOAT,
                timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session  (session_id),
                INDEX idx_intent   (intent_detected),
                INDEX idx_ts       (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        # ── intents — response_text langsung di sini, tidak ada tabel responses ──
        cur.execute('''
            CREATE TABLE IF NOT EXISTS intents (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                intent_name   VARCHAR(100) NOT NULL UNIQUE,
                patterns      TEXT NOT NULL  COMMENT 'JSON array',
                response_text TEXT NOT NULL  COMMENT 'Teks jawaban chatbot',
                quick_replies TEXT           COMMENT 'JSON array tombol quick reply',
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')

        conn.commit(); cur.close(); conn.close()
        print("[DB] MySQL siap.")

    # =================================================================
    # CONVERSATION LOGS
    # =================================================================
    def log_conversation(self, session_id, user_message, bot_response, intent, confidence, response_time):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('''
            INSERT INTO conversation_logs
                (session_id,user_message,bot_response,intent_detected,confidence,response_time)
            VALUES (%s,%s,%s,%s,%s,%s)
        ''', (session_id, user_message, bot_response, intent, confidence, response_time))
        conn.commit(); mid = cur.lastrowid; cur.close(); conn.close()
        return mid

    def get_conversation_logs(self, limit=100, offset=0):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT id,session_id,user_message,bot_response,
                   intent_detected AS intent,confidence,response_time,timestamp
            FROM conversation_logs ORDER BY timestamp DESC LIMIT %s OFFSET %s
        ''', (limit, offset))
        rows = cur.fetchall(); cur.close(); conn.close()
        return [self._fmt_row(r, ['timestamp']) for r in rows]

    def get_sessions_list(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT session_id,
                   MIN(timestamp) AS first_time, MAX(timestamp) AS last_time,
                   COUNT(*) AS total_messages,
                   GROUP_CONCAT(DISTINCT intent_detected ORDER BY intent_detected SEPARATOR ',') AS intents_raw
            FROM conversation_logs GROUP BY session_id ORDER BY last_time DESC
        ''')
        rows = cur.fetchall(); cur.close(); conn.close()
        result = []
        for r in rows:
            intents = [i.strip() for i in (r['intents_raw'] or '').split(',') if i.strip()]
            result.append({
                'session_id':     r['session_id'],
                'first_time':     self._fmt(r['first_time']),
                'last_time':      self._fmt(r['last_time']),
                'total_messages': r['total_messages'],
                'intents_used':   intents
            })
        return result

    def get_session_detail(self, session_id):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT id,user_message,bot_response,intent_detected AS intent,
                   confidence,response_time,timestamp
            FROM conversation_logs WHERE session_id=%s ORDER BY timestamp ASC
        ''', (session_id,))
        rows = cur.fetchall(); cur.close(); conn.close()
        if not rows: return None
        msgs = [self._fmt_row(r, ['timestamp']) for r in rows]
        intents_used = list(dict.fromkeys(m['intent'] for m in msgs if m['intent']))
        return {
            'session_id': session_id, 'messages': msgs,
            'summary': {
                'total_messages': len(msgs),
                'first_time':     msgs[0]['timestamp'],
                'last_time':      msgs[-1]['timestamp'],
                'intents_used':   intents_used
            }
        }

    def get_all_logs_for_backup(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT id,session_id,user_message,bot_response,
                   intent_detected AS intent,confidence,response_time,timestamp
            FROM conversation_logs ORDER BY timestamp ASC
        ''')
        rows = cur.fetchall(); cur.close(); conn.close()
        return [self._fmt_row(r, ['timestamp']) for r in rows]

    def delete_all_logs(self):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('DELETE FROM conversation_logs')
        deleted = cur.rowcount; conn.commit(); cur.close(); conn.close()
        return deleted

    def delete_session_logs(self, session_id):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('DELETE FROM conversation_logs WHERE session_id=%s', (session_id,))
        deleted = cur.rowcount; conn.commit(); cur.close(); conn.close()
        return deleted

    def search_logs(self, search_query, intent_filter=None):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        sql = '''SELECT id,session_id,user_message,bot_response,
                        intent_detected AS intent,confidence,response_time,timestamp
                 FROM conversation_logs WHERE (user_message LIKE %s OR bot_response LIKE %s)'''
        params = [f'%{search_query}%', f'%{search_query}%']
        if intent_filter:
            sql += ' AND intent_detected=%s'; params.append(intent_filter)
        sql += ' ORDER BY timestamp DESC LIMIT 50'
        cur.execute(sql, params); rows = cur.fetchall(); cur.close(); conn.close()
        return [self._fmt_row(r, ['timestamp']) for r in rows]

    # =================================================================
    # ANALYTICS
    # =================================================================
    def get_analytics_summary(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('SELECT COUNT(DISTINCT session_id) AS total FROM conversation_logs')
        tc = cur.fetchone()['total']
        cur.execute('SELECT COUNT(*) AS total FROM conversation_logs')
        tm = cur.fetchone()['total']
        cur.execute('SELECT AVG(response_time) AS avg FROM conversation_logs')
        art = cur.fetchone()['avg'] or 0
        cur.execute('''
            SELECT intent_detected AS intent, COUNT(*) AS count
            FROM conversation_logs WHERE intent_detected IS NOT NULL
            GROUP BY intent_detected ORDER BY count DESC
        ''')
        top_intents = cur.fetchall()
        cur.execute('''
            SELECT DATE(timestamp) AS date, COUNT(*) AS count
            FROM conversation_logs WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(timestamp) ORDER BY date
        ''')
        mpd = []
        for r in cur.fetchall():
            mpd.append({'date': r['date'].strftime('%Y-%m-%d') if hasattr(r['date'],'strftime') else r['date'], 'count': r['count']})
        cur.execute('SELECT AVG(confidence) AS avg FROM conversation_logs WHERE confidence IS NOT NULL')
        ac = cur.fetchone()['avg'] or 0
        cur.close(); conn.close()
        return {
            'total_conversations': tc, 'total_messages': tm,
            'avg_response_time':   round(float(art), 3),
            'avg_confidence':      round(float(ac), 2),
            'top_intents': top_intents, 'messages_per_day': mpd
        }

    def get_hourly_activity(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT HOUR(timestamp) AS hour, COUNT(*) AS count
            FROM conversation_logs WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY HOUR(timestamp) ORDER BY hour
        ''')
        rows = cur.fetchall(); cur.close(); conn.close()
        hmap = {r['hour']: r['count'] for r in rows}
        return [{'hour': h, 'count': hmap.get(h, 0)} for h in range(24)]

    def get_intent_confidence_stats(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT intent_detected AS intent,
                   ROUND(AVG(confidence),3) AS avg_confidence, COUNT(*) AS count
            FROM conversation_logs
            WHERE intent_detected IS NOT NULL AND confidence IS NOT NULL
            GROUP BY intent_detected ORDER BY avg_confidence ASC
        ''')
        rows = cur.fetchall(); cur.close(); conn.close()
        return rows

    # =================================================================
    # INTENTS — response_text langsung di tabel ini
    # =================================================================
    def get_all_intents(self):
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM intents ORDER BY intent_name')
        rows = cur.fetchall(); cur.close(); conn.close()
        for r in rows:
            r['patterns']      = json.loads(r['patterns'])      if r['patterns']      else []
            r['quick_replies'] = json.loads(r['quick_replies'])  if r['quick_replies'] else []
            self._fmt_row(r, ['created_at','updated_at'])
        return rows

    def get_intent_by_name(self, intent_name):
        """Dipakai oleh RuleEngine untuk ambil response_text."""
        conn = self.get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM intents WHERE intent_name=%s', (intent_name,))
        row = cur.fetchone(); cur.close(); conn.close()
        if row:
            row['patterns']      = json.loads(row['patterns'])      if row['patterns']      else []
            row['quick_replies'] = json.loads(row['quick_replies'])  if row['quick_replies'] else []
        return row

    def add_intent(self, intent_name, patterns, response_text, quick_replies=None):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('''
            INSERT INTO intents (intent_name, patterns, response_text, quick_replies)
            VALUES (%s,%s,%s,%s)
        ''', (intent_name,
              json.dumps(patterns, ensure_ascii=False),
              response_text,
              json.dumps(quick_replies or [], ensure_ascii=False)))
        conn.commit(); cur.close(); conn.close()

    def update_intent(self, old_name, intent_name, patterns, response_text, quick_replies=None):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('''
            UPDATE intents SET intent_name=%s, patterns=%s, response_text=%s, quick_replies=%s
            WHERE intent_name=%s
        ''', (intent_name,
              json.dumps(patterns, ensure_ascii=False),
              response_text,
              json.dumps(quick_replies or [], ensure_ascii=False),
              old_name))
        conn.commit(); cur.close(); conn.close()

    def delete_intent(self, intent_name):
        conn = self.get_connection(); cur = conn.cursor()
        cur.execute('DELETE FROM intents WHERE intent_name=%s', (intent_name,))
        conn.commit(); cur.close(); conn.close()