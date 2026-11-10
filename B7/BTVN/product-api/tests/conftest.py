from contextlib import contextmanager

import pytest
from sqlalchemy import event

from product_api.config import TestConfig
from product_api.extensions import db
from product_api.factory import create_app


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@contextmanager
def count_queries():
    """Ghi lại mọi câu SQL chạy trong khối with — dùng để phát hiện N+1."""
    statements = []

    def _on_execute(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", _on_execute)
    try:
        yield statements
    finally:
        event.remove(db.engine, "before_cursor_execute", _on_execute)


def make_product(client, sku, qty=100, price=1000):
    r = client.post(
        "/api/v1/products",
        json={"sku": sku, "name": f"Product {sku}", "price_cents": price, "qty_in_stock": qty},
    )
    assert r.status_code == 201, r.json
    return r.json
