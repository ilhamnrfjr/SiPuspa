from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
import uuid
import json
import os
from functools import wraps
from nlu_engine import NLUEngine
from rule_engine import RuleEngine
from database import Database
from auth import AuthSystem
import csv
import io

app = Flask(__name__)
CORS(app)  # Enable CORS untuk frontend

# Initialize components
nlu = NLUEngine()
rule_engine = RuleEngine()
db = Database()
auth = AuthSystem()

# Path ke folder frontend dan dashboard
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
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
# DECORATOR UNTUK PROTECTED ROUTES
# =====================================================

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split('Bearer ')[1]
        
        user = auth.verify_token(token)
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'Token invalid atau expired'}), 401
        
        request.user = user
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# AUTH ENDPOINTS
# =====================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username dan password harus diisi'}), 400
        
        result = auth.login(username, password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
    
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify token masih valid"""
    return jsonify({
        'valid': True,
        'user': request.user
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout endpoint"""
    try:
        token = request.headers.get('Authorization').split('Bearer ')[1]
        auth.logout(token)
        return jsonify({'success': True, 'message': 'Logout berhasil'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change password"""
    try:
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        result = auth.change_password(request.user['id'], old_password, new_password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# CHATBOT ENDPOINTS (PUBLIC)
# =====================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        start_time = time.time()
        
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process dengan NLU
        nlu_result = nlu.process(user_message)
        
        # Generate response dengan Rule Engine
        response = rule_engine.get_response(
            intent=nlu_result['intent'],
            entities=nlu_result['entities'],
            session_id=session_id
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log ke database
        db.log_conversation(
            session_id=session_id,
            user_message=user_message,
            bot_response=response['text'],
            intent=nlu_result['intent'],
            confidence=nlu_result['confidence'],
            response_time=response_time
        )
        
        return jsonify({
            'session_id': session_id,
            'message': response['text'],
            'quick_replies': response['quick_replies'],
            'intent': nlu_result['intent'],
            'confidence': round(nlu_result['confidence'], 2),
            'response_time': round(response_time, 3),
            'entities': nlu_result['entities']
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Maaf, terjadi kesalahan. Silakan coba lagi.'
        }), 500

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Endpoint untuk feedback pengguna"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        rating = data.get('rating')
        feedback_text = data.get('feedback_text', '')
        
        if not all([session_id, rating]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        db.save_feedback(session_id, message_id, rating, feedback_text)
        
        return jsonify({
            'status': 'success',
            'message': 'Terima kasih atas feedback Anda!'
        })
    
    except Exception as e:
        print(f"Error in feedback endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# ADMIN DASHBOARD ENDPOINTS (PROTECTED)
# =====================================================

@app.route('/api/admin/analytics/summary', methods=['GET'])
@require_auth
def get_analytics_summary():
    """Get analytics summary untuk dashboard"""
    try:
        summary = db.get_analytics_summary()
        return jsonify(summary)
    except Exception as e:
        print(f"Error in analytics summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    

@app.route('/api/admin/analytics/hourly', methods=['GET'])
@require_auth
def get_hourly_activity():
    try:
        data = db.get_hourly_activity()
        return jsonify({'hourly': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/analytics/confidence', methods=['GET'])
@require_auth
def get_intent_confidence_stats():
    try:
        data = db.get_intent_confidence_stats()
        return jsonify({'confidence_stats': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/logs/sessions', methods=['GET'])
@require_auth
def get_sessions_list():
    """Daftar session (1 baris per session) untuk tabel Conversation Logs"""
    try:
        sessions = db.get_sessions_list()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/logs/session/<session_id>', methods=['GET'])
@require_auth
def get_session_detail(session_id):
    try:
        detail = db.get_session_detail(session_id)
        if not detail:
            return jsonify({'error': 'Session tidak ditemukan'}), 404
        return jsonify(detail)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/logs/backup', methods=['GET'])
@require_auth
def backup_logs():
    """Download semua log sebagai CSV"""
    try:
        import csv, io
        logs = db.get_all_logs_for_backup()
 
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'session_id', 'user_message', 'bot_response',
            'intent', 'confidence', 'response_time', 'timestamp'
        ])
        writer.writeheader()
        writer.writerows(logs)
 
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': 'attachment; filename=chatbot_logs_backup.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/logs/all', methods=['DELETE'])
@require_auth
def delete_all_logs():
    try:
        deleted = db.delete_all_logs()
        return jsonify({'success': True, 'deleted': deleted, 'message': f'{deleted} pesan berhasil dihapus'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@app.route('/api/admin/logs/session/<session_id>', methods=['DELETE'])
@require_auth
def delete_session_logs(session_id):
    try:
        deleted = db.delete_session_logs(session_id)
        if deleted == 0:
            return jsonify({'error': 'Session tidak ditemukan'}), 404
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# INTENT MANAGEMENT ENDPOINTS (PROTECTED)
# =====================================================

@app.route('/api/admin/intents', methods=['GET'])
@require_auth
def get_intents():
    """Get semua intents dari file intents.json"""
    try:
        with open('data/intents.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'intents': data['intents']})
    except Exception as e:
        print(f"Error getting intents: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/intents', methods=['POST'])
@require_auth
def add_intent():
    """Tambah intent baru"""
    try:
        data = request.json
        
        # Validasi input
        required_fields = ['intent', 'patterns', 'response_key']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load existing intents
        with open('data/intents.json', 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        
        # Check duplicate
        if any(i['intent'] == data['intent'] for i in intents_data['intents']):
            return jsonify({'error': 'Intent sudah ada'}), 400
        
        # Add new intent
        new_intent = {
            'intent': data['intent'],
            'patterns': data['patterns'],
            'entities': data.get('entities', []),
            'response_key': data['response_key']
        }
        
        intents_data['intents'].append(new_intent)
        
        # Save to file
        with open('data/intents.json', 'w', encoding='utf-8') as f:
            json.dump(intents_data, f, indent=2, ensure_ascii=False)
        
        # Reload NLU engine
        global nlu
        nlu = NLUEngine()
        
        return jsonify({
            'success': True,
            'message': 'Intent berhasil ditambahkan',
            'intent': new_intent
        })
    
    except Exception as e:
        print(f"Error adding intent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/intents/<intent_name>', methods=['PUT'])
@require_auth
def update_intent(intent_name):
    """Update intent"""
    try:
        data = request.json
        
        # Load existing intents
        with open('data/intents.json', 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        
        # Find and update intent
        intent_found = False
        for i, intent in enumerate(intents_data['intents']):
            if intent['intent'] == intent_name:
                intents_data['intents'][i] = {
                    'intent': data.get('intent', intent_name),
                    'patterns': data.get('patterns', intent['patterns']),
                    'entities': data.get('entities', intent.get('entities', [])),
                    'response_key': data.get('response_key', intent['response_key'])
                }
                intent_found = True
                break
        
        if not intent_found:
            return jsonify({'error': 'Intent tidak ditemukan'}), 404
        
        # Save to file
        with open('data/intents.json', 'w', encoding='utf-8') as f:
            json.dump(intents_data, f, indent=2, ensure_ascii=False)
        
        # Reload NLU engine
        global nlu
        nlu = NLUEngine()
        
        return jsonify({
            'success': True,
            'message': 'Intent berhasil diupdate'
        })
    
    except Exception as e:
        print(f"Error updating intent: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/intents/<intent_name>', methods=['DELETE'])
@require_auth
def delete_intent(intent_name):
    """Delete intent"""
    try:
        # Load existing intents
        with open('data/intents.json', 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        
        # Filter out the intent to delete
        original_count = len(intents_data['intents'])
        intents_data['intents'] = [i for i in intents_data['intents'] if i['intent'] != intent_name]
        
        if len(intents_data['intents']) == original_count:
            return jsonify({'error': 'Intent tidak ditemukan'}), 404
        
        # Save to file
        with open('data/intents.json', 'w', encoding='utf-8') as f:
            json.dump(intents_data, f, indent=2, ensure_ascii=False)
        
        # Reload NLU engine
        global nlu
        nlu = NLUEngine()
        
        return jsonify({
            'success': True,
            'message': 'Intent berhasil dihapus'
        })
    
    except Exception as e:
        print(f"Error deleting intent: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# RESPONSE MANAGEMENT ENDPOINTS (PROTECTED)
# =====================================================

@app.route('/api/admin/responses', methods=['GET'])
@require_auth
def get_responses():
    """Get semua responses dari file responses.json"""
    try:
        with open('data/responses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'responses': data['responses']})
    except Exception as e:
        print(f"Error getting responses: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/responses/<response_key>', methods=['GET'])
@require_auth
def get_response_detail(response_key):
    """Get detail response berdasarkan key"""
    try:
        with open('data/responses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if response_key in data['responses']:
            return jsonify({
                'key': response_key,
                'response': data['responses'][response_key]
            })
        else:
            return jsonify({'error': 'Response tidak ditemukan'}), 404
    except Exception as e:
        print(f"Error getting response detail: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/responses/<response_key>', methods=['PUT'])
@require_auth
def update_response(response_key):
    """Update response"""
    try:
        data = request.json
        
        # Load existing responses
        with open('data/responses.json', 'r', encoding='utf-8') as f:
            responses_data = json.load(f)
        
        # Update atau create response
        responses_data['responses'][response_key] = {
            'text': data.get('text', ''),
            'quick_replies': data.get('quick_replies', [])
        }
        
        # Save to file
        with open('data/responses.json', 'w', encoding='utf-8') as f:
            json.dump(responses_data, f, indent=2, ensure_ascii=False)
        
        # Reload Rule engine
        global rule_engine
        rule_engine = RuleEngine()
        
        return jsonify({
            'success': True,
            'message': 'Response berhasil diupdate'
        })
    
    except Exception as e:
        print(f"Error updating response: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/responses/<response_key>', methods=['DELETE'])
@require_auth
def delete_response(response_key):
    """Delete response"""
    try:
        # Load existing responses
        with open('data/responses.json', 'r', encoding='utf-8') as f:
            responses_data = json.load(f)
        
        if response_key not in responses_data['responses']:
            return jsonify({'error': 'Response tidak ditemukan'}), 404
        
        # Delete response
        del responses_data['responses'][response_key]
        
        # Save to file
        with open('data/responses.json', 'w', encoding='utf-8') as f:
            json.dump(responses_data, f, indent=2, ensure_ascii=False)
        
        # Reload Rule engine
        global rule_engine
        rule_engine = RuleEngine()
        
        return jsonify({
            'success': True,
            'message': 'Response berhasil dihapus'
        })
    
    except Exception as e:
        print(f"Error deleting response: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# FAQ MANAGEMENT ENDPOINTS (PROTECTED)
# =====================================================

@app.route('/api/admin/faq', methods=['GET'])
@require_auth
def get_faq():
    """Get daftar FAQ"""
    try:
        faqs = db.get_faq_list()
        return jsonify({'faqs': faqs})
    except Exception as e:
        print(f"Error in get FAQ: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/faq', methods=['POST'])
@require_auth
def add_faq():
    """Tambah FAQ baru"""
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')
        category = data.get('category', 'Umum')
        
        if not all([question, answer]):
            return jsonify({'error': 'Question and answer required'}), 400
        
        faq_id = db.add_faq(question, answer, category)
        
        return jsonify({
            'status': 'success',
            'faq_id': faq_id,
            'message': 'FAQ berhasil ditambahkan'
        })
    except Exception as e:
        print(f"Error in add FAQ: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/faq/<int:faq_id>', methods=['PUT'])
@require_auth
def update_faq(faq_id):
    """Update FAQ"""
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')
        category = data.get('category')
        
        if not all([question, answer, category]):
            return jsonify({'error': 'All fields required'}), 400
        
        db.update_faq(faq_id, question, answer, category)
        
        return jsonify({
            'status': 'success',
            'message': 'FAQ berhasil diupdate'
        })
    except Exception as e:
        print(f"Error in update FAQ: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/faq/<int:faq_id>', methods=['DELETE'])
@require_auth
def delete_faq(faq_id):
    """Delete FAQ (soft delete)"""
    try:
        db.delete_faq(faq_id)
        
        return jsonify({
            'status': 'success',
            'message': 'FAQ berhasil dihapus'
        })
    except Exception as e:
        print(f"Error in delete FAQ: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Chatbot API is running',
        'version': '1.0.0'
    })

@app.route('/api', methods=['GET'])
def api_info():
    """API info endpoint"""
    return jsonify({
        'message': 'Chatbot Perpustakaan BPK RI API',
        'version': '1.0.0',
        'endpoints': {
            'chat': '/api/chat',
            'health': '/api/health',
            'login': '/api/auth/login',
            'dashboard': '/api/admin/analytics/summary'
        }
    })

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Chatbot Perpustakaan BPK RI")
    print("=" * 60)
    print()
    print("📊 Dashboard: http://localhost:5000")
    print("💬 Chat API:  http://localhost:5000/api/chat")
    print("🔐 Chatbot:   http://localhost:5000/chatbot")
    print()
    print("🔑 Default Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("=" * 60)
    print("✅ Server is running on http://localhost:5000")
    print("=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)