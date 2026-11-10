from tests.conftest import make_product


def test_create_product_ok(client):
    r = client.post(
        "/api/v1/products", json={"sku": "PEN-01", "name": "Pen", "price_cents": 1500}
    )
    assert r.status_code == 201
    assert r.json["sku"] == "PEN-01"
    assert r.json["qty_in_stock"] == 0  # mặc định
    assert r.json["archived"] is False


def test_create_product_duplicate_sku_409(client):
    make_product(client, "PEN-01")
    r = client.post(
        "/api/v1/products", json={"sku": "PEN-01", "name": "Other", "price_cents": 1}
    )
    assert r.status_code == 409
    assert r.json["error"] == "conflict"


def test_create_product_invalid_422(client):
    r = client.post("/api/v1/products", json={"sku": "A", "name": "", "price_cents": -1})
    assert r.status_code == 422
    assert set(r.json["detail"]) == {"sku", "name", "price_cents"}


def test_list_pagination(client):
    for i in range(5):
        make_product(client, f"SKU-{i}")
    r = client.get("/api/v1/products?page=2&size=2")
    assert r.status_code == 200
    assert r.json["page"] == 2 and r.json["size"] == 2 and r.json["total"] == 5
    assert [p["sku"] for p in r.json["items"]] == ["SKU-2", "SKU-3"]


def test_get_404(client):
    r = client.get("/api/v1/products/9999")
    assert r.status_code == 404
    assert r.json["error"] == "not_found"


def test_reserve(client):
    p = make_product(client, "BOOK-1", qty=2)
    r = client.post(f"/api/v1/products/{p['id']}/reserve", json={"qty": 2})
    assert r.status_code == 200 and r.json["qty_in_stock"] == 0
    r = client.post(f"/api/v1/products/{p['id']}/reserve", json={"qty": 1})
    assert r.status_code == 409 and r.json["error"] == "out_of_stock"


def test_patch_only_changes_sent_fields(client):
    p = make_product(client, "CUP-1", price=500)
    r = client.patch(f"/api/v1/products/{p['id']}", json={"price_cents": 700})
    assert r.status_code == 200
    assert r.json["price_cents"] == 700 and r.json["name"] == p["name"]


def test_soft_delete(client):
    p = make_product(client, "OLD-1")
    assert client.delete(f"/api/v1/products/{p['id']}").status_code == 204
    assert client.get(f"/api/v1/products/{p['id']}").status_code == 404
    assert client.get("/api/v1/products").json["total"] == 0
