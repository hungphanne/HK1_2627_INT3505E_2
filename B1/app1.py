# app1.py - Bài 1: Hellp API
from flask import Flask
app1 = Flask(__name__)
@app1.route('/')
def index():
    return {'message': 'Hello API'}
if __name__ == '__main__':
    app1.run(host='127.0.0.1', port=5000, debug=True)