from tests.conftest import count_queries, make_product


def _order(client, *product_ids):
    return client.post(
        "/api/v1/orders",
        json={"customer_name": "An", "items": [{"product_id": i, "qty": 1} for i in product_ids]},
    )


def test_create_order_reduces_stock(client):
    a = make_product(client, "A-1", qty=5)
    b = make_product(client, "B-1", qty=5)
    r = _order(client, a["id"], b["id"])
    assert r.status_code == 201
    assert len(r.json["items"]) == 2
    assert client.get(f"/api/v1/products/{a['id']}").json["qty_in_stock"] == 4


def test_create_order_out_of_stock_is_all_or_nothing(client):
    a = make_product(client, "A-1", qty=5)
    b = make_product(client, "B-1", qty=0)
    r = _order(client, a["id"], b["id"])
    assert r.status_code == 409
    # item A không bị trừ kho vì cả đơn bị rollback
    assert client.get(f"/api/v1/products/{a['id']}").json["qty_in_stock"] == 5


def test_get_order_eager_loading(client):
    a = make_product(client, "A-1")
    b = make_product(client, "B-1")
    order_id = _order(client, a["id"], b["id"]).json["id"]

    with count_queries() as queries:
        r = client.get(f"/api/v1/orders/{order_id}")
    assert r.status_code == 200
    assert {i["product"]["sku"] for i in r.json["items"]} == {"A-1", "B-1"}
    # 1 query lấy order + 1 query selectinload items (JOIN product)
    assert len(queries) <= 2, queries


def test_list_orders_no_n_plus_1(client):
    products = [make_product(client, f"P-{i}") for i in range(3)]
    ids = [p["id"] for p in products]

    for _ in range(2):
        _order(client, *ids)
    with count_queries() as few:
        client.get("/api/v1/orders")

    for _ in range(8):
        _order(client, *ids)
    with count_queries() as many:
        r = client.get("/api/v1/orders")

    assert len(r.json["items"]) == 10
    # Số query KHÔNG tăng theo số order => không có N+1
    assert len(many) == len(few), many
