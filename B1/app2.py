from flask import Flask, jsonify, request
app2 = Flask(__name__)

@app2.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app2.route('/echo', methods=['POST'])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({"you_sent": data}), 200
if __name__ == '__main__':
    app2.run(host='127.0.0.1', port=5000, debug=True)