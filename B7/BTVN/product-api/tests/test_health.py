def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200 and r.json["checks"]["db"] == "ok"
