from flask import Flask, jsonify, request

app6 = Flask(__name__)
_next = 1
BOOKS = [{"id": 1, "title": "Clean Code", "author": "R. Martin"}]

def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)

@app6.route("/books", methods=["GET"])
def list_books():
    n = int(request.args.get("limit", 100))
    return jsonify(BOOKS[:n]), 200

@app6.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

@app6.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a = body.get("title"), body.get("author")
    if not t or not a:
        return jsonify({"error": "need title + author"}), 400
    book = {"id": _next, "title": t, "author": a}
    _next += 1; BOOKS.append(book)
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

@app6.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    if request.method == "PUT":
        book.update(request.get_json(silent=True) or {})
        return jsonify(book), 200
    BOOKS.remove(book)
    return "", 204

if __name__ == "__main__":
    app6.run(host="127.0.0.1", port=5000, debug=True)