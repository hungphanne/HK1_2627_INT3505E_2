"""Shared fixtures for all exercises; each test receives a fresh SQLite database."""
import pytest
from app import create_app
from models import Book, db


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_book(app):
    with app.app_context():
        book = Book(title="API Design Patterns", author="J.J. Geewax", year=2021)
        db.session.add(book)
        db.session.commit()
        return book.id
