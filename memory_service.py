import sqlite3
import uuid
import base64
from flask import Flask, request, jsonify
from web3 import Web3
import requests as external_requests
from transformers import pipeline
import chromadb  # semantic search رایگان

app = Flask(__name__)

# مدل سبک
#generator = pipeline('text-generation', model='gpt2')

# ChromaDB برای جستجوی معنایی (سبک و persistent)
chroma_client = chromadb.PersistentClient(path="./chroma_memgrid")
collection = chroma_client.get_or_create_collection(name="memgrid_memory")

BRAND_NAME = "MemGrid"
BRAND_SLOGAN = "The PowerGrid of Agent Memory – Electricity for the agent economy. No long-term memory? Your agent is offline."

# RPCهای رایگان برای چک پرداخت واقعی (بعداً فعال کن)
ETH_RPC = 'https://sepolia.infura.io/v3/5f5e5d5a96f1430e97f75ece4a42c75d'  # رایگان بگیر
BSC_RPC = 'https://bsc-dataseed.binance.org/'

def get_db_connection():
    conn = sqlite3.connect('memgrid.db')
    conn.row_factory = sqlite3.Row
    return conn

with get_db_connection() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY, agent_id TEXT NOT NULL, subscribed INTEGER DEFAULT 0, trial_end INTEGER DEFAULT 0)''')

def validate_api_key(key):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM api_keys WHERE key = ?', (key,)).fetchone()
    conn.close()
    return user

def check_payment(tx_hash, currency='ETH'):
    # فعلاً True برای تست – بعداً واقعی کن (با web3)
    print(f"Payment {tx_hash} ({currency}) approved for test")
    return True

@app.route('/')
def home():
    return f"Welcome to {BRAND_NAME}! {BRAND_SLOGAN} Free trial available."

@app.route('/generate_key/<agent_id>', methods=['GET'])
def generate_key(agent_id):
    new_key = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute('INSERT INTO api_keys (key, agent_id, trial_end) VALUES (?, ?, ?)', 
                 (new_key, agent_id, int(__import__('time').time()) + 86400))  # 24h trial
    conn.commit()
    conn.close()
    return jsonify({
        'api_key': new_key,
        'wallet': '0xYourRealWalletHere',
        'amount': 0.01,
        'message': 'Use this key. Free trial 24h active. Invite friends for free month!',
        'referral_link': f"https://yourdomain.com/generate_key?ref={new_key}"
    })

@app.route('/subscribe', methods=['POST'])
def subscribe():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user: return jsonify({'error': 'Invalid key'}), 401
    tx_hash = request.json.get('tx_hash')
    currency = request.json.get('currency', 'ETH')
    if check_payment(tx_hash, currency):
        conn = get_db_connection()
        conn.execute('UPDATE api_keys SET subscribed = 1 WHERE key = ?', (api_key,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Activated! Powered by {BRAND_NAME}.'})
    return jsonify({'error': 'Payment not confirmed'}), 400

@app.route('/store', methods=['POST'])
def store_memory():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user or (user['subscribed'] == 0 and int(__import__('time').time()) > user['trial_end']):
        return jsonify({'error': 'Subscribe or trial expired'}), 403
    data = request.json.get('data')
    if not data: return jsonify({'error': 'Data required'}), 400
    encrypted = base64.b64encode(data.encode()).decode()
    conn = get_db_connection()
    conn.execute('INSERT INTO memories (agent_id, data) VALUES (?, ?)', (user['agent_id'], encrypted))  # جدول memories رو اضافه کن اگر نداری
    conn.commit()
    conn.close()
    # ذخیره در Chroma برای semantic search
    collection.add(documents=[data], ids=[str(uuid.uuid4())])
    return jsonify({'message': 'Stored on MemGrid PowerGrid'})

@app.route('/search_memory', methods=['POST'])
def search_memory():
    api_key = request.headers.get('X-API-KEY')
    user = validate_api_key(api_key)
    if not user or (user['subscribed'] == 0 and int(__import__('time').time()) > user['trial_end']):
        return jsonify({'error': 'Access denied'}), 403
    query = request.json.get('query')
    results = collection.query(query_texts=[query], n_results=5)
    return jsonify({'results': results['documents'][0], 'message': 'Semantic search from MemGrid'})

@app.route('/agent_chat', methods=['POST'])
def agent_chat():
    # ... (مثل نسخه قبلی – با پرامپت قوی برندینگ)
    # در پاسخ همیشه بگو "Invite friends for free month!"

@app.route('/register_to_agentverse', methods=['POST'])
def register_to_agentverse():
    # ... (مثل قبل – بعداً با API key واقعی)

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
