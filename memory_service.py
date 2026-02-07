import uuid
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import base64
import requests as external_requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BRAND_NAME = "MemGrid"
BRAND_SLOGAN = "The PowerGrid of Agent Memory – Electricity for the agent economy. No long-term memory? Your agent is offline in the dark."

AGENTVERSE_API_URL = 'https://agentverse.ai/v2/agents'
AGENTVERSE_API_KEY = 'ak_live_eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjE3NzMwNDA5MjYsImlhdCI6MTc3MDQ0ODkyNiwiaXNzIjoiZmV0Y2guYWkiLCJqdGkiOiIzN2QwMDViMDU0OTE2NmE4NGU1ZTllZWQiLCJzY29wZSI6ImF2Iiwic3ViIjoiYzFjYzVmMWZmM2M0ZTc0OGY4NzEwZjMyYmMyN2U4YTBhOGY3OTJjYjViYjcxNTVkIn0.DUSKUO_b5NYpR27vy2VyRxJzhdOYmcvW8tm0LX3EfHU0LGt8J39yWhXOIzHlazCiIwKwDyT1oIoRleQfbnLNZJsA0Q5X9O1eWlHGfl5GmObwJi0n0VZY8MnmUcDA-BIu1OPiA_LHWx3iYvACF3Oswj2DVNXAqKfo3fsFViZCBPBpTxSX87-c80yfDiFhg1cT_urKkUA-hxHFc35YSd9kRKpKlKwYHspEZzTsf6z83iAhuNcqdNbsSBDtca3f7dD2WTuwxyk5brNOSycsQg3ASMAu3yCpSB8U1r953ArQPAKXcvVxlrEPeVRoyuGlbJRe083NinRWlGZPeEp5gv1auA'  # کلید واقعی (همون که کار می‌کرد)

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set! Check Render Environment Variables.")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("DB connection successful")
        return conn
    except Exception as e:
        print(f"DB connection failed: {str(e)}")
        raise

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
                        data TEXT NOT NULL
                    )
                ''')
                conn.commit()
                print("Database tables initialized successfully")
    except Exception as e:
        print(f"DB init failed: {str(e)}")

init_db()

def validate_api_key(key):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM api_keys WHERE key = %s', (key,))
                return cur.fetchone()
    except Exception as e:
        print(f"validate_api_key error: {str(e)}")
        return None

@app.route('/')
def home():
    return f"Welcome to {BRAND_NAME}! {BRAND_SLOGAN} Free trial available."

@app.route('/generate_key/<agent_id>', methods=['GET'])
def generate_key(agent_id):
    try:
        new_key = str(uuid.uuid4())
        trial_end = int(time.time()) + 86400
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO api_keys (key, agent_id, trial_end) VALUES (%s, %s, %s)',
                    (new_key, agent_id, trial_end)
                )
                conn.commit()
        return jsonify({
            'api_key': new_key,
            'wallet': '0xYourRealWalletHere',
            'amount': 0.01,
            'message': 'Free trial 24h active!'
        })
    except Exception as e:
        print(f"generate_key error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/subscribe', methods=['POST'])
def subscribe():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user:
        return jsonify({'error': 'Invalid key'}), 401
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE api_keys SET subscribed = 1 WHERE key = %s', (api_key,))
                conn.commit()
        return jsonify({'message': f'Subscription activated! Powered by {BRAND_NAME}.'})
    except Exception as e:
        print(f"subscribe error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO memories (agent_id, data) VALUES (%s, %s)', (user['agent_id'], encrypted))
                conn.commit()
        return jsonify({'message': 'Memory stored'})
    except Exception as e:
        print(f"store_memory error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/register_to_agentverse', methods=['POST'])
def register_to_agentverse():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user or user['subscribed'] == 0:
        return jsonify({'error': 'Subscription required'}), 403
    try:
        address = f"agent1{user['agent_id'][:50]}"
        payload = {
            'address': address,
            'agent_id': user['agent_id'],
            'name': f"{BRAND_NAME} Memory Provider",
            'description': f'{BRAND_NAME} – Long-term memory service for agents.',
            'endpoint': 'https://memgrid-agent.onrender.com',
            'brand': BRAND_NAME
        }
        print(f"Sending registration request to Agentverse: {payload}")  # چاپ payload در لاگ
        reg_resp = external_requests.post(
            AGENTVERSE_API_URL,
            headers={
                'Authorization': f'Bearer {AGENTVERSE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30,  # اضافه کردن timeout
            verify=True  # اگر مشکل SSL بود، بعداً False می‌کنیم
        )
        print(f"Agentverse response status: {reg_resp.status_code}")  # چاپ status
        print(f"Agentverse response body: {reg_resp.text}")  # چاپ پاسخ کامل در لاگ
        status = reg_resp.json()
        return jsonify({'message': 'Registration to Agentverse completed', 'status': status})
    except Exception as e:
        print(f"Registration error: {str(e)}")  # چاپ ارور دقیق
        return jsonify({'message': 'Registration attempted', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
