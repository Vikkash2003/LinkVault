import os
import random
import string
import time
import psycopg2
from flask import Flask, request, jsonify, redirect, abort
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn


def init_db():
    retries = 5
    while retries > 0:
        try:
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
            print("Database initialised successfully")
            return
        except Exception as e:
            retries -= 1
            print(f"Database not ready, retrying in 2 seconds... ({e})")
            time.sleep(2)
    print("Could not connect to database after 5 retries")


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "url field is required"}), 400

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
        conn = get_db()
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
    app.run(host='0.0.0.0', port=5000, debug=True)