"""Teaching Books API for UET.IT3298, session 8.

Run locally: python -m app --port 5000
Authentication in this starter is intentionally a DEMO, not a security model.
"""
import argparse
import os
from pathlib import Path

from flask import Flask, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate
from sqlalchemy.exc import IntegrityError

from models import Book, db


class BookInput(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    author = fields.String(required=True, validate=validate.Length(min=1, max=200))
    year = fields.Integer(allow_none=True, validate=validate.Range(min=1450, max=2100))
    isbn = fields.String(allow_none=True, validate=validate.Regexp(r"^\d{13}$"))


book_schema = BookInput()


def create_app(config=None, cfg=None):
    """Application factory. ``cfg`` is accepted for lecture-code compatibility."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + str(Path("instance/books.db").resolve()),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
        TESTING=False,
    )
    app.config.update(config or cfg or {})
    db.init_app(app)

    with app.app_context():
        db.create_all()

    def error(status, code, message, errors=None):
        payload = {"code": code, "message": message}
        if errors is not None:
            payload["errors"] = errors
        return jsonify(payload), status

    def parse_book():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError({"body": ["Expected a JSON object."]})
        return book_schema.load(data)

    @app.errorhandler(ValidationError)
    def handle_validation(exc):
        details = [
            {"field": field, "message": "; ".join(map(str, messages))}
            for field, messages in exc.messages.items()
        ]
        return error(400, "VALIDATION_ERROR", "Invalid book data", details)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/books")
    def list_books():
        query = Book.query.order_by(Book.id)
        if author := request.args.get("author"):
            query = query.filter_by(author=author)
        if request.args.get("year") is not None:
            try:
                year = int(request.args["year"])
            except ValueError:
                return error(400, "VALIDATION_ERROR", "year must be an integer", [
                    {"field": "year", "message": "Expected an integer."}
                ])
            query = query.filter_by(year=year)
        try:
            page = int(request.args.get("page", "1"))
        except ValueError:
            return error(400, "VALIDATION_ERROR", "page must be an integer", [
                {"field": "page", "message": "Expected an integer."}
            ])
        if page < 1:
            return error(400, "VALIDATION_ERROR", "page must be >= 1", [
                {"field": "page", "message": "Must be >= 1."}
            ])
        size = 20
        books = query.offset((page - 1) * size).limit(size).all()
        return jsonify([book.to_dict() for book in books])

    @app.get("/books/<book_id>")
    def get_book(book_id):
        if not book_id.isdecimal() or int(book_id) < 1:
            return error(400, "INVALID_ID", "Book id must be a positive integer")
        book = db.session.get(Book, int(book_id))
        if book is None:
            return error(404, "NOT_FOUND", "Book not found")
        return jsonify(book.to_dict())

    @app.post("/books")
    def create_book():
        data = parse_book()
        book = Book(**data)
        db.session.add(book)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return error(409, "CONFLICT", "ISBN already exists")
        return jsonify(book.to_dict()), 201, {"Location": f"/books/{book.id}"}

    @app.put("/books/<book_id>")
    def update_book(book_id):
        if not book_id.isdecimal() or int(book_id) < 1:
            return error(400, "INVALID_ID", "Book id must be a positive integer")
        book = db.session.get(Book, int(book_id))
        if book is None:
            return error(404, "NOT_FOUND", "Book not found")
        data = parse_book()
        # PUT replaces optional values when omitted.
        for field in ("title", "author", "year", "isbn"):
            setattr(book, field, data.get(field))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return error(409, "CONFLICT", "ISBN already exists")
        return jsonify(book.to_dict())

    @app.delete("/books/<book_id>")
    def delete_book(book_id):
        if not book_id.isdecimal() or int(book_id) < 1:
            return error(400, "INVALID_ID", "Book id must be a positive integer")
        book = db.session.get(Book, int(book_id))
        if book is None:
            return error(404, "NOT_FOUND", "Book not found")
        db.session.delete(book)
        db.session.commit()
        return "", 204

    @app.post("/auth/login")
    def demo_login():
        """Optional demo endpoint for slide 29, NOT production authentication."""
        data = request.get_json(silent=True) or {}
        user = os.environ.get("LAB_DEMO_USER", "lab")
        password = os.environ.get("LAB_DEMO_PASSWORD", "lab")
        if data.get("user") == user and data.get("pwd") == password:
            return jsonify(token="LOCAL_DEMO_TOKEN_DO_NOT_USE_IN_PRODUCTION")
        return error(401, "UNAUTHORIZED", "Invalid demo credentials")

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    application = create_app()
    application.run(host="127.0.0.1", port=args.port, debug=False)
