"""Baseline smoke tests shipped with the starter (not the Lab 1 solution)."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_book_can_be_created(client):
    response = client.post("/books", json={"title": "Book", "author": "Author"})
    assert response.status_code == 201
    assert isinstance(response.get_json()["id"], int)
