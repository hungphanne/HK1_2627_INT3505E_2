import sqlite3
from flask import Flask, jsonify

app = Flask(__name__)
DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Bảng books
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        )
    """)

    # Bảng orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    """)

    # Thêm dữ liệu mẫu
    cursor.execute(
        "INSERT OR IGNORE INTO books (id, title, author) VALUES (1, 'Clean Code', 'Robert C. Martin')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO books (id, title, author) VALUES (2, 'The Pragmatic Programmer', 'Andrew Hunt')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO orders (id, book_id, quantity, status) VALUES (1, 1, 2, 'completed')"
    )

    conn.commit()
    conn.close()
    print("-> Database initialized!")


# ==================== ORDERS ENDPOINTS ====================

@app.get("/orders/")
def get_orders():
    """Lấy danh sách tất cả các đơn hàng."""
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders]), 200


@app.get("/orders/<int:oid>")
def get_order(oid):
    """Lấy chi tiết một đơn hàng theo ID."""
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    conn.close()

    if order is None:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(dict(order)), 200


# ==================== BOOKS ENDPOINTS ====================

@app.get("/books/")
def get_books():
    """Lấy danh sách sách từ SQLite."""
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return jsonify([dict(book) for book in books]), 200


if __name__ == "__main__":
    init_db() 
    app.run(debug=True, port=5000)