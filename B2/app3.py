from flask import Flask, jsonify, request, make_response

app3 = Flask(__name__)

DEFAULT_SIZE, MAX_SIZE = 20, 100

BOOKS = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"id": 3, "title": "1984", "author": "George Orwell"},
    {"id": 4, "title": "Pride and Prejudice", "author": "Jane Austen"},
    {"id": 5, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"id": 6, "title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"id": 7, "title": "Fahrenheit 451", "author": "Ray Bradbury"},
    {"id": 8, "title": "Moby-Dick", "author": "Herman Melville"},
    {"id": 9, "title": "War and Peace", "author": "Leo Tolstoy"},
    {"id": 10, "title": "The Odyssey", "author": "Homer"},
    {"id": 11, "title": "Crime and Punishment", "author": "Fyodor Dostoevsky"},
    {"id": 12, "title": "The Brothers Karamazov", "author": "Fyodor Dostoevsky"},
    {"id": 13, "title": "Brave New World", "author": "Aldous Huxley"},
    {"id": 14, "title": "The Divine Comedy", "author": "Dante Alighieri"},
    {"id": 15, "title": "The Iliad", "author": "Orwell"},
    {"id": 16, "title": "Don Quixote", "author": "Miguel de Cervantes"},
    {"id": 17, "title": "One Hundred Years of Solitude", "author": "Gabriel Garcia Marquez"},
    {"id": 18, "title": "The Stranger", "author": "Albert Camus"},
    {"id": 19, "title": "The Trial", "author": "Franz Kafka"},
    {"id": 20, "title": "The Metamorphosis", "author": "Franz Kafka"},
]

@app3.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify({"error": "Page and size must be integers"}), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    flt = BOOKS
    a = request.args.get("author")
    if a:
        flt = [b for b in flt if b["author"].lower() == a.lower()]

    q = (request.args.get("q") or "").lower()
    if q:
        flt = [b for b in flt if q in b["title"].lower()]

    total = len(flt)
    start = (page - 1) * size
    end = start + size
    items = flt[start:end]
    last = (total + size - 1) // size

    def u(p):
        return f"/books?page={p}&size={size}"
    links = {
        "self": {"href": u(page)},
        "first": {"href": u(1)},
        "last": {"href": u(max(1, last))}}

    if page > 1:
        links["prev"] = {"href": u(page - 1)}
    if end < total:
        links["next"] = {"href": u(page + 1)}
    body = {"data" : items,
            "pagination": {"page": page, "size": size, "total": total, "last": last},
            "_links": links}
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp

if __name__ == "__main__":
    app3.run(debug=True, port=5000)   

           