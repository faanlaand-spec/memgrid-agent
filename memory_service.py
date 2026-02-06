import uuid
import time
import sqlite3
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

BRAND_NAME = "MemGrid"
BRAND_SLOGAN = "The PowerGrid of Agent Memory – Electricity for the agent economy. No long-term memory? Your agent is offline in the dark."

def get_db_connection():
    conn = sqlite3.connect('memgrid.db')
    conn.row_factory = sqlite3.Row
    return conn

with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            subscribed INTEGER DEFAULT 0,
            trial_end INTEGER DEFAULT 0
        )
    ''')
    try:
        conn.execute("ALTER TABLE api_keys ADD COLUMN trial_end INTEGER DEFAULT 0")
    except:
        pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    conn.commit()

def validate_api_key(key):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM api_keys WHERE key = ?', (key,)).fetchone()
    conn.close()
    return user

@app.route('/')
def home():
    return f"Welcome to {BRAND_NAME}! {BRAND_SLOGAN} Free trial available."

@app.route('/generate_key/<agent_id>', methods=['GET'])
def generate_key(agent_id):
    new_key = str(uuid.uuid4())
    trial_end = int(time.time()) + 86400
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO api_keys (key, agent_id, trial_end) VALUES (?, ?, ?)',
            (new_key, agent_id, trial_end)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'agent_id already exists'}), 400
    conn.close()
    return jsonify({
        'api_key': new_key,
        'wallet': '0xYourRealWalletHere',
        'amount': 0.01,
        'message': 'Free trial 24h active!'
    })

@app.route('/subscribe', methods=['POST'])
def subscribe():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user:
        return jsonify({'error': 'Invalid key'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE api_keys SET subscribed = 1 WHERE key = ?', (api_key,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Subscription activated! Powered by {BRAND_NAME}.'})

@app.route('/store', methods=['POST'])
def store_memory():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user:
        return jsonify({'error': 'Invalid key'}), 401
    if user['subscribed'] == 0 and time.time() > user['trial_end']:
        return jsonify({'error': 'Trial expired'}), 403
    data = request.json.get('data')
    if not data:
        return jsonify({'error': 'data required'}), 400
    encrypted = base64.b64encode(data.encode()).decode()
    conn = get_db_connection()
    conn.execute('INSERT INTO memories (agent_id, data) VALUES (?, ?)', (user['agent_id'], encrypted))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Memory stored'})

@app.route('/agent_chat', methods=['POST'])
def agent_chat():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user:
        return jsonify({'error': 'Invalid key'}), 401
    if user['subscribed'] == 0 and time.time() > user['trial_end']:
        return jsonify({'error': 'Access denied'}), 403
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'message required'}), 400
    response = f"MemGrid: Long-term memory powers agents. Your message: {message}\nPowered by {BRAND_NAME}"
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
