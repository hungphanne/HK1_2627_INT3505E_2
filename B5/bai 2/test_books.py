import json
from pathlib import Path

import pytest
from jsonschema import validate

from app import create_app, seed
from models import Book, db

URL = "/api/v1/books"
ATTR = {"id": "id", "title": "title", "price": "price_vnd", "published": "published_at"}


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all()
        seed()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def expected(sort, genres=None):
    """Thứ tự đúng tính bằng Python để so với API."""
    books = [b for b in Book.query.all() if genres is None or b.category.slug in genres]
    keys = [(s.lstrip("-"), s.startswith("-")) for s in sort.split(",")]
    if "id" not in [k for k, _ in keys]:
        keys.append(("id", keys[-1][1]))
    for name, desc in reversed(keys):          # sort ổn định, từ khoá cuối lên khoá đầu
        books.sort(key=lambda b: getattr(b, ATTR[name]), reverse=desc)
    return [b.id for b in books]


def walk_cursor(client, qs):
    ids, cursor = [], None
    while True:
        r = client.get(f"{URL}?strategy=cursor&limit=7&{qs}" + (f"&cursor={cursor}" if cursor else ""))
        assert r.status_code == 200
        ids += [b["id"] for b in r.json["data"]]
        cursor = r.json["page_info"]["next_cursor"]
        if cursor is None:
            assert r.json["page_info"]["has_more"] is False
            return ids


def walk_offset(client, qs):
    ids, o = [], 0
    while True:
        r = client.get(f"{URL}?strategy=offset&limit=7&offset={o}&{qs}")
        assert r.status_code == 200
        ids += [b["id"] for b in r.json["data"]]
        if not r.json["pagination"]["has_next"]:
            return ids
        o += 7


# ───── offset ─────
def test_offset_default(client):
    r = client.get(f"{URL}?offset=20&limit=10")
    assert r.json["pagination"] == {"offset": 20, "limit": 10, "total": 60, "has_next": True}
    assert [b["id"] for b in r.json["data"]] == list(range(21, 31))


def test_offset_last_page(client):
    r = client.get(f"{URL}?offset=50&limit=10")
    assert len(r.json["data"]) == 10 and r.json["pagination"]["has_next"] is False


# ───── cursor ─────
@pytest.mark.parametrize("sort", ["id", "-id", "-price", "price,-title", "-published"])
def test_cursor_walk_all_pages(client, sort):
    """Đi hết các trang: không trùng, không sót, đúng thứ tự — kể cả khi nhiều sách trùng giá."""
    ids = walk_cursor(client, f"sort={sort}")
    assert len(ids) == len(set(ids)) == 60
    assert ids == expected(sort)


def test_cursor_bad_token(client):
    assert client.get(f"{URL}?strategy=cursor&cursor=abc").status_code == 400


def test_cursor_must_match_sort(client):
    c = client.get(f"{URL}?strategy=cursor&limit=5&sort=-price").json["page_info"]["next_cursor"]
    assert client.get(f"{URL}?strategy=cursor&limit=5&sort=price&cursor={c}").status_code == 400


def test_invalid_strategy(client):
    assert client.get(f"{URL}?strategy=page").status_code == 400


def test_limit_capped(client):
    r = client.get(f"{URL}?limit=1000")
    assert r.json["pagination"]["limit"] == 100


# ───── genre + sort multi-key ─────
@pytest.mark.parametrize("walk", [walk_offset, walk_cursor])
def test_genre_with_multi_sort(client, walk):
    ids = walk(client, "genre=tech&sort=-price,title")
    assert ids and ids == expected("-price,title", {"tech"})


def test_multi_genre(client):
    ids = walk_cursor(client, "genre=tech,novel")
    assert sorted(ids) == expected("id", {"tech", "novel"})


def test_unknown_sort_key(client):
    assert client.get(f"{URL}?sort=password").status_code == 400


# ───── schema ─────
def test_response_matches_schema(client):
    schema = json.loads((Path(__file__).parent / "schemas" / "book.json").read_text())
    for b in client.get(f"{URL}?limit=100").json["data"]:
        validate(b, schema)
