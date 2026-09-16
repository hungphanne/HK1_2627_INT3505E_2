from flask import Flask, jsonify, request, make_response

app1 = Flask(__name__)

BOOKS = []
_next_id = 1

@app1.get('/books')
def get_books():
    return jsonify({
        "data": BOOKS,
        "total": len(BOOKS)
    }), 200

@app1.post('/books')
def add_book():
    global _next_id
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    p = request.get_json(silent=True) or {}
    t = p.get("title", "").strip()
    a = p.get("author", "").strip()

    if not t or not a:
        return jsonify({"error": "Title and author are required"}), 422

    book = {"id": _next_id, "title": t, "author": a}
    BOOKS.append(book); _next_id += 1

    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp

if __name__ == "__main__":
    app1.run(debug=True)