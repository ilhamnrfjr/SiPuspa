from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import time, uuid, os, csv, io
from datetime import datetime
from functools import wraps
from nlu_engine import NLUEngine
from rule_engine import RuleEngine
from database import Database
from auth import AuthSystem

app = Flask(__name__)
CORS(app)

nlu         = NLUEngine()
rule_engine = RuleEngine()
db          = Database()
auth        = AuthSystem()

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR  = os.path.join(BASE_DIR, '..', 'frontend')
DASHBOARD_DIR = os.path.join(BASE_DIR, '..', 'dashboard')

# =====================================================
# STATIC FILE SERVING
# =====================================================

@app.route('/')
def index():
    return send_from_directory(DASHBOARD_DIR, 'admin-dashboard.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory(DASHBOARD_DIR, 'admin-dashboard.html')

@app.route('/chatbot')
def chatbot():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/dashboard/<path:filename>')
def dashboard_static(filename):
    return send_from_directory(DASHBOARD_DIR, filename)

@app.route('/frontend/<path:filename>')
def frontend_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# =====================================================
# DECORATORS
# =====================================================

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
            token = token.split('Bearer ')[1]
        user = auth.verify_token(token)
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'Token invalid atau expired'}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated


# =====================================================
# AUTH ENDPOINTS
# =====================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username dan password harus diisi'}), 400
        result = auth.login(data['username'], data['password'])
        return jsonify(result), (200 if result['success'] else 401)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    return jsonify({'valid': True, 'user': request.user})

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    try:
        token = request.headers.get('Authorization', '').split('Bearer ')[1]
        auth.logout(token)
        return jsonify({'success': True, 'message': 'Logout berhasil'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    try:
        data   = request.json
        result = auth.change_password(request.user['id'], data.get('old_password'), data.get('new_password'))
        return jsonify(result), (200 if result['success'] else 400)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# CHATBOT (PUBLIC)
# =====================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        start      = time.time()
        data       = request.json
        user_msg   = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        if not user_msg:
            return jsonify({'error': 'Message is required'}), 400
        nlu_result = nlu.process(user_msg)
        response   = rule_engine.get_response(nlu_result['intent'], nlu_result['entities'], session_id)
        rt         = time.time() - start
        db.log_conversation(session_id, user_msg, response['text'],
                            nlu_result['intent'], nlu_result['confidence'], rt)
        return jsonify({
            'session_id':   session_id,
            'message':      response['text'],
            'quick_replies':response['quick_replies'],
            'intent':       nlu_result['intent'],
            'confidence':   round(nlu_result['confidence'], 2),
            'response_time':round(rt, 3),
            'entities':     nlu_result['entities']
        })
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': 'Internal server error', 'message': 'Maaf, terjadi kesalahan.'}), 500

# =====================================================
# ANALYTICS
# =====================================================

@app.route('/api/admin/analytics/summary', methods=['GET'])
@require_auth
def get_analytics_summary():
    try: return jsonify(db.get_analytics_summary())
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics/hourly', methods=['GET'])
@require_auth
def get_hourly_activity():
    try: return jsonify({'hourly': db.get_hourly_activity()})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics/confidence', methods=['GET'])
@require_auth
def get_intent_confidence_stats():
    try: return jsonify({'confidence_stats': db.get_intent_confidence_stats()})
    except Exception as e: return jsonify({'error': str(e)}), 500

# =====================================================
# CONVERSATION LOGS
# =====================================================

@app.route('/api/admin/logs/sessions', methods=['GET'])
@require_auth
def get_sessions_list():
    try: return jsonify({'sessions': db.get_sessions_list()})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/session/<session_id>', methods=['GET'])
@require_auth
def get_session_detail(session_id):
    try:
        detail = db.get_session_detail(session_id)
        if not detail: return jsonify({'error': 'Session tidak ditemukan'}), 404
        return jsonify(detail)
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/backup', methods=['GET'])
@require_auth
def backup_logs():
    try:
        logs   = db.get_all_logs_for_backup()
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        writer.writerow(['No','Session ID','Waktu','Pesan Pengguna','Respons Bot',
                         'Intent Terdeteksi','Confidence Score','Response Time (s)'])
        for idx, log in enumerate(logs, 1):
            writer.writerow([
                idx,
                log.get('session_id', ''),
                log.get('timestamp', ''),
                log.get('user_message', ''),
                log.get('bot_response', ''),
                log.get('intent', ''),
                f"{round(float(log.get('confidence') or 0) * 100, 1)}%",
                f"{round(float(log.get('response_time') or 0), 3)}"
            ])
        fname = f"backup_percakapan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output.getvalue().encode('utf-8-sig'),
            mimetype='text/csv; charset=utf-8-sig',
            headers={'Content-Disposition': f'attachment; filename={fname}'}
        )
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/all', methods=['DELETE'])
@require_auth
def delete_all_logs():
    try:
        deleted = db.delete_all_logs()
        return jsonify({'success': True, 'deleted': deleted, 'message': f'{deleted} pesan dihapus'})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/session/<session_id>', methods=['DELETE'])
@require_auth
def delete_session_logs(session_id):
    try:
        deleted = db.delete_session_logs(session_id)
        if deleted == 0: return jsonify({'error': 'Session tidak ditemukan'}), 404
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e: return jsonify({'error': str(e)}), 500

# =====================================================
# INTENT MANAGEMENT
# =====================================================

@app.route('/api/admin/intents', methods=['GET'])
@require_auth
def get_intents():
    try: return jsonify({'intents': db.get_all_intents()})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/intents', methods=['POST'])
@require_auth
def add_intent():
    try:
        d = request.json
        db.add_intent(
            intent_name   = d['intent_name'],
            patterns      = d['patterns'],
            response_text = d['response_text'],
            quick_replies = d.get('quick_replies', [])
        )
        global nlu; nlu = NLUEngine()
        return jsonify({'success': True, 'message': 'Intent ditambahkan'})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/intents/<intent_name>', methods=['PUT'])
@require_auth
def update_intent(intent_name):
    try:
        d = request.json
        db.update_intent(
            old_name      = intent_name,
            intent_name   = d['intent_name'],
            patterns      = d['patterns'],
            response_text = d['response_text'],
            quick_replies = d.get('quick_replies', [])
        )
        global nlu; nlu = NLUEngine()
        return jsonify({'success': True, 'message': 'Intent diupdate'})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/admin/intents/<intent_name>', methods=['DELETE'])
@require_auth
def delete_intent(intent_name):
    try:
        db.delete_intent(intent_name)
        global nlu; nlu = NLUEngine()
        return jsonify({'success': True, 'message': 'Intent dihapus'})
    except Exception as e: return jsonify({'error': str(e)}), 500


# =====================================================
# UTILITY
# =====================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Chatbot API is running', 'version': '2.0.0'})

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({'message': 'Chatbot Perpustakaan BPK RI API', 'version': '2.0.0'})

@app.errorhandler(404)
def not_found(error): return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error): return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Chatbot Perpustakaan BPK RI")
    print("=" * 60)
    print("📊 Dashboard : http://localhost:5000")
    print("💬 Chat API  : http://localhost:5000/api/chat")
    print("🔐 Chatbot   : http://localhost:5000/chatbot")
    print("🔑 Login     : admin / admin123  (superadmin)")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)