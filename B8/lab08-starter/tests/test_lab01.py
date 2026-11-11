"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
import copy

import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


# ---------------------------------------------------------------- helpers
def to_json_schema(node):
    """Convert OpenAPI 3.0 ``nullable: true`` into plain JSON Schema.

    jsonschema ignores ``nullable``, so ``{type: string, nullable: true}``
    would reject ``null``. We rewrite it to ``{type: [string, "null"]}``.
    """
    if isinstance(node, dict):
        node = {k: to_json_schema(v) for k, v in node.items()}
        if node.pop("nullable", False) and "type" in node:
            types = node["type"] if isinstance(node["type"], list) else [node["type"]]
            node["type"] = types + ["null"]
        return node
    if isinstance(node, list):
        return [to_json_schema(item) for item in node]
    return node



# ---------------------------------------------------------------- A
def test_list_books_empty_db_returns_empty_array(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.is_json
    body = response.get_json()
    assert body is not None          # not null
    assert isinstance(body, list)
    assert body == []


# ---------------------------------------------------------------- B
def test_get_nonexistent_book_returns_404_not_found(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "NOT_FOUND"


# ---------------------------------------------------------------- C
def test_create_book_missing_title_returns_400_with_title_error(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["code"] == "VALIDATION_ERROR"
    error_fields = [err["field"] for err in body["errors"]]
    assert "title" in error_fields

# ---------------------------------------------------------------- D
def test_deleted_book_is_no_longer_found(client):
    created = client.post(
        "/books", json={"title": "Clean Code", "author": "Robert C. Martin"}
    )
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    deleted = client.delete(f"/books/{book_id}")
    assert deleted.status_code == 204
    assert deleted.data == b""

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"
