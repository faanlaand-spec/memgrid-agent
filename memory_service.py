import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

BRAND_NAME = "MemGrid"
BRAND_SLOGAN = "The PowerGrid of Agent Memory – Electricity for the agent economy."

@app.route('/')
def home():
    return f"Welcome to {BRAND_NAME}! {BRAND_SLOGAN} Free trial available."

@app.route('/generate_key/<agent_id>', methods=['GET'])
def generate_key(agent_id):
    new_key = str(uuid.uuid4())
    return jsonify({
        'api_key': new_key,
        'wallet': '0xYourRealWalletAddressHere',  # بعداً واقعی کن
        'amount': 0.01,
        'message': 'Free trial 24h active. Use this key for testing. Subscribe for unlimited memory!'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'brand': BRAND_NAME,
        'message': 'MemGrid service is running and ready.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
