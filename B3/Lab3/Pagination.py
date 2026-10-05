import base64
import json
import random
from datetime import datetime, timedelta

from flask import Flask, request, abort

app = Flask(__name__)
app.json.sort_keys = False

# Mock data: 30 orders
random.seed(42)
ORDERS = [
    {
        "id": i,
        "customer_id": random.choice([101, 102, 103, 104]),
        "status": random.choice(["pending", "paid", "shipped", "cancelled"]),
        "total": round(random.uniform(10, 500), 2),
        "created_at": (datetime(2026, 9, 1) + timedelta(hours=7 * i)).isoformat(),
    }
    for i in range(1, 31)
]


# Cursor = base64(JSON{"v": giá trị sort của bản ghi cuối, "id": id cuối})
def encode_cursor(value, last_id):
    raw = json.dumps({"v": value, "id": last_id}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor):
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return data["v"], int(data["id"])
    except Exception:
        abort(400, description="Invalid cursor")


@app.get("/orders")
def list_orders():
    limit = request.args.get("limit", 10, type=int)
    sort = request.args.get("sort", "id")
    sort_field = sort.lstrip("-")
    desc = sort.startswith("-")

    # (2) filter
    rows = ORDERS
    if status := request.args.get("status"):
        rows = [o for o in rows if o["status"] == status]
    if customer_id := request.args.get("customer_id", type=int):
        rows = [o for o in rows if o["customer_id"] == customer_id]

    # (3) sort - kèm id làm tie-breaker để thứ tự luôn ổn định
    key = lambda o: (o[sort_field], o["id"])
    rows = sorted(rows, key=key, reverse=desc)

    # (1) cursor: chỉ lấy các bản ghi đứng SAU bản ghi cuối của trang trước
    if cursor := request.args.get("cursor"):
        last = decode_cursor(cursor)
        rows = [o for o in rows if (key(o) < last if desc else key(o) > last)]

    page = rows[:limit]
    has_more = len(rows) > limit
    next_cursor = encode_cursor(page[-1][sort_field], page[-1]["id"]) if has_more else None

    # (4) sparse fieldsets
    if fields := request.args.get("fields"):
        wanted = fields.split(",")
        page = [{f: o[f] for f in wanted if f in o} for o in page]

    return {"data": page, "next_cursor": next_cursor, "has_more": has_more}


if __name__ == "__main__":
    app.run(debug=True)