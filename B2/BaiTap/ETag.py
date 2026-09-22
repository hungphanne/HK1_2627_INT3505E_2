import hashlib
import json
import sqlite3
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)
DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def calculate_record_etag(title: str, author: str) -> str:
    """Tạo ETag hash MD5 từ nội dung bản ghi sách."""
    content = f"{title}|{author}".encode("utf-8")
    return hashlib.md5(content).hexdigest()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Bảng books bổ sung cột etag
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            etag TEXT
        )
    """)

    # Seed data kèm tính toán etag
    sample_books = [
        (1, "Clean Code", "Robert C. Martin"),
        (2, "The Pragmatic Programmer", "Andrew Hunt"),
    ]

    for bid, title, author in sample_books:
        etag = calculate_record_etag(title, author)
        cursor.execute(
            """
            INSERT OR IGNORE INTO books (id, title, author, etag) 
            VALUES (?, ?, ?, ?)
        """,
            (bid, title, author, etag),
        )

    conn.commit()
    conn.close()


# ==================== BOOKS ENDPOINTS ====================

@app.get("/books")
@app.get("/books/")
def get_books():
    conn = get_db_connection()
    books = conn.execute("SELECT id, title, author, etag FROM books ORDER BY id ASC").fetchall()
    conn.close()

    # 1. Tính toán ETag tổng thể cho toàn bộ collection /books/
    # Kết hợp các etag của từng cuốn sách lại thành 1 chuỗi hash đại diện
    combined_etags = "".join([book["etag"] or "" for book in books])
    collection_etag = f'"{hashlib.md5(combined_etags.encode("utf-8")).hexdigest()}"'

    # 2. Kiểm tra header If-None-Match từ client gửi lên
    client_etag = request.headers.get("If-None-Match")

    # 3. Nếu ETag trùng khớp -> Trả về 304 Not Modified (không kèm body)
    if client_etag and client_etag.strip() == collection_etag:
        res = make_response("", 304)
        res.headers["ETag"] = collection_etag
        return res

    # 4. Nếu không khớp hoặc gọi lần đầu -> Trả về JSON kèm header ETag
    books_data = [
        {"id": b["id"], "title": b["title"], "author": b["author"]}
        for b in books
    ]
    res = make_response(jsonify(books_data), 200)
    res.headers["ETag"] = collection_etag
    return res

@app.post("/books")
@app.post("/books/")
def create_book():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    author = data.get("author")

    if not title or not author:
        return jsonify({"error": "Missing title or author"}), 400

    etag = calculate_record_etag(title, author)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO books (title, author, etag) VALUES (?, ?, ?)",
        (title, author, etag),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id, "title": title, "author": author}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)