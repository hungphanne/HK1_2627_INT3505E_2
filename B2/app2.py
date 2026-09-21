from flask import Flask, jsonify, request, make_response

app2 = Flask(__name__)

BOOKS = [{"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "isbn": "9780743273565", "price": 10.99},
         {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee", "isbn": "9780061120084", "price": 7.99}]

@app2.get("/books/<int:bid>")
def fetch(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None: return jsonify(error = "not found"), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60"; 
    return resp

@app2.put("/books/<int:bid>")
def put(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None: return jsonify(error = "not found"), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify({"error": "Title and author are required"}), 422
    BOOKS[i]= {"id": bid, "title": t.strip(), "author": a.strip(),
               "isbn": p.get("isbn"), "price": p.get("price")}
    return jsonify(BOOKS[i]), 200

@app2.patch("/books/<int:bid>")
def patch(bid):
    i = next((k for k, b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None: return jsonify(error = "not found"), 404
    p = request.get_json(silent=True) or {}
    if p.get("price", 0) < 0:
        return jsonify({"error": "Price must be positive"}), 422
    for k in "title author isbn price".split():
        if k in p: BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200

@app2.delete("/books/<int:bid>")
def delete(bid):
    i = next((k for k, b in enumerate(BOOKS) 
        if b["id"] == bid), None)
    if i is None: return jsonify(error = "not found"), 404
    BOOKS.pop(i);
    return"", 204

if __name__ == "__main__":
    app2.run(debug=True, port=5000)