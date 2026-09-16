from flask import Flask, jsonify, request
app4 = Flask(__name__)

BOOKS = [
    {"id": "abc-1", "title": "Hoc Lap Trinh Python", "author": "Nguyen Van A"},
    {"id": "abc-2", "title": "Flask Web Development", "author": "Miguel Grinberg"},
    {"id": "abc-3", "title": "Kien Truc Huong Dich Vu", "author": "Tran Van B"},
]

def find_by_id(book_id):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None

# Route 1: Query string (bộ lọc / phân trang)
@app4.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["title"].lower()]
    return jsonify({"items": items[:limit]}), 200

# Route 2: Path param tìm theo ID
@app4.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# Route 3: Path param ép kiểu int
@app4.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"id":item_id}), 200

if __name__ == "__main__":
    app4.run(port=5000, debug=True)