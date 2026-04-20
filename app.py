import os
import random
import string
import psycopg2
from flask import Flask, request, jsonify, redirect, abort
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

#connection to POSTGRESQL database
def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

# Initialize the database and create the links table if it doesn't exist
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@app.route('/health',methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/shorten', methods = ['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    original_url = data['url']
    code = generate_code()

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO links (code, original_url) VALUES (%s, %s)",
            (code, original_url)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    short_url = f"http://localhost:5000/{code}"
    return jsonify({"short_url": short_url, "code": code}), 201

@app.route('/<code>', methods=['GET'])
def redirect_url(code):
    try:
        conn =get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT original_url FROM links WHERE code = %s",
            (code,)

        )
        result = cur.fetchone()
        cur.close()
        conn.close()        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if result is None:
        abort(404)
    
    return redirect(result[0], code=302)
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
