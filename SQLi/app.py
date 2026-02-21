from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "users.db"

# ── khởi tạo database ──────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("""
        CREATE TABLE users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL,
            email    TEXT NOT NULL
        )
    """)
    c.executemany("INSERT INTO users (username, password, role, email) VALUES (?,?,?,?)", [
        ("admin",   "SuperSecret123", "admin",  "admin@company.com"),
        ("alice",   "alice2024",      "user",   "alice@company.com"),
        ("bob",     "bobpassword",    "user",   "bob@company.com"),
        ("charlie", "charlie99",      "user",   "charlie@company.com"),
    ])
    conn.commit()
    conn.close()

# ── helper ─────────────────────────────────────────────────────────────────
def dict_rows(cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

# ── VULNERABLE endpoint (SQLi) ─────────────────────────────────────────────
@app.route("/api/login/vulnerable", methods=["POST"])
def login_vulnerable():
    data     = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    # ⚠️  NỐI CHUỖI TRỰC TIẾP — dễ bị SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    try:
        c.execute(query)
        rows = dict_rows(c)
        conn.close()
        if rows:
            return jsonify({
                "success": True,
                "message": f"Đăng nhập thành công! Xin chào {rows[0]['username']} ({rows[0]['role']})",
                "user":    rows[0],
                "query":   query,
                "rows_returned": len(rows)
            })
        else:
            return jsonify({
                "success": False,
                "message": "Sai tên đăng nhập hoặc mật khẩu.",
                "query":   query,
                "rows_returned": 0
            }), 401
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Lỗi SQL!",
            "error":   str(e),
            "query":   query
        }), 500

# ── SECURE endpoint (Parameterized Query) ──────────────────────────────────
@app.route("/api/login/secure", methods=["POST"])
def login_secure():
    data     = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    # ✅  DÙNG PARAMETERIZED QUERY — an toàn
    query = "SELECT * FROM users WHERE username = ? AND password = ?"

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(query, (username, password))
    rows = dict_rows(c)
    conn.close()

    display_query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    if rows:
        return jsonify({
            "success": True,
            "message": f"Đăng nhập thành công! Xin chào {rows[0]['username']} ({rows[0]['role']})",
            "user":    rows[0],
            "query":   display_query,
            "rows_returned": len(rows)
        })
    else:
        return jsonify({
            "success": False,
            "message": "Sai tên đăng nhập hoặc mật khẩu.",
            "query":   display_query,
            "rows_returned": 0
        }), 401

# ── serve frontend ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    init_db()
    print("✅  Database khởi tạo xong!")
    print("🚀  Server chạy tại http://localhost:5000")
    app.run(debug=True, port=5000)