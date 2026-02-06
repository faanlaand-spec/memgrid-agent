import uuid
import time
import base64
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import requests as external_requests

app = Flask(__name__)

BRAND_NAME = "MemGrid"
BRAND_SLOGAN = "The PowerGrid of Agent Memory – Electricity for the agent economy."

# Postgres Connection
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        subscribed INTEGER DEFAULT 0,
                        trial_end BIGINT DEFAULT 0
                    )
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id SERIAL PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print("DB Init Error:", e)

# Initialize database on startup
init_db()

def validate_api_key(key):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM api_keys WHERE key = %s", (key,))
            return cur.fetchone()

# ====================== Routes ======================

@app.route('/')
def home():
    return f"Welcome to {BRAND_NAME}! {BRAND_SLOGAN} Free trial available."

@app.route('/generate_key/<agent_id>', methods=['GET'])
def generate_key(agent_id):
    new_key = str(uuid.uuid4())
    trial_end = int(time.time()) + 86400
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO api_keys (key, agent_id, trial_end) VALUES (%s, %s, %s)",
                    (new_key, agent_id, trial_end)
                )
                conn.commit()
            except:
                return jsonify({'error': 'agent_id already exists'}), 400

    return jsonify({
        'api_key': new_key,
        'wallet': '0xYourRealWalletHere',
        'amount': 0.01,
        'message': 'Free trial 24h active! Subscribe for unlimited memory.'
    })

@app.route('/subscribe', methods=['POST'])
def subscribe():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user:
        return jsonify({'error': 'Invalid key'}), 401

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE api_keys SET subscribed = 1 WHERE key = %s", (api_key,))
            conn.commit()

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

    encrypted = base64.b64encode(data.encode('utf-8')).decode('utf-8')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO memories (agent_id, data) VALUES (%s, %s)",
                (user['agent_id'], encrypted)
            )
            conn.commit()

    return jsonify({'message': 'Memory stored successfully on the PowerGrid'})

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

    response = (
        f"As {BRAND_NAME}, I remember everything for you. "
        f"Long-term memory is the electricity that keeps agents alive. "
        f"Your message: {message}\n\nPowered by {BRAND_NAME}"
    )
    return jsonify({'response': response})

@app.route('/register_to_agentverse', methods=['POST'])
def register_to_agentverse():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user or user['subscribed'] == 0:
        return jsonify({'error': 'Subscription required'}), 403

    try:
        payload = {
            'agent_id': user['agent_id'],
            'name': f"{BRAND_NAME} Memory Provider",
            'description': f'{BRAND_NAME} – Long-term memory service essential for agents.',
            'endpoint': 'https://memgrid-agent.onrender.com',
            'brand': BRAND_NAME
        }
        reg_resp = external_requests.post(
            "https://api.agentverse.ai/agents/register",
            headers={'Authorization': f'Bearer {AGENTVERSE_API_KEY}'},
            json=payload
        )
        status = reg_resp.json()
    except Exception as e:
        status = {'status': 'Registration attempted', 'error': str(e)}

    return jsonify({'message': 'Registered to Agentverse!', 'status': status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
