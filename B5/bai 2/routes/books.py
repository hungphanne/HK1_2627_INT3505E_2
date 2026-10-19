import base64
import json
from datetime import date

from flask import Blueprint, abort, jsonify, request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from models import Book, Category, db

bp = Blueprint("books", __name__)

DEFAULT, MAX_ = 20, 100
# whitelist: tên trong ?sort= → cột
SORTABLE = {"id": Book.id, "title": Book.title, "price": Book.price_vnd,
            "published": Book.published_at}


def bad_request(message):
    resp = jsonify({"error": "bad_request", "message": message})
    resp.status_code = 400
    abort(resp)


def encode(s):
    return base64.urlsafe_b64encode(json.dumps(s).encode()).decode().rstrip("=")


def decode(t):
    pad = "=" * (-len(t) % 4)
    return json.loads(base64.urlsafe_b64decode(t + pad))


def parse_sort(raw):
    """'-price,title' → [("price", True), ("title", False), ("id", False)].
    Luôn kết thúc bằng id để thứ tự là deterministic (tie-break)."""
    keys = []
    for part in raw.split(","):
        name, desc = part.strip().lstrip("-"), part.strip().startswith("-")
        if name not in SORTABLE:
            bad_request(f"sort key không hợp lệ: {name!r}")
        if name in [k for k, _ in keys]:
            bad_request(f"sort key bị lặp: {name!r}")
        keys.append((name, desc))
        if name == "id":            # id unique → các khoá sau không còn tác dụng
            return keys
    keys.append(("id", keys[-1][1]))
    return keys


def after_cursor(keys, values):
    """Composite cursor nhiều khoá, mỗi khoá có thể khác hướng:
    (k1 ▷ v1) OR (k1 = v1 AND k2 ▷ v2) OR ...   ▷ là < nếu DESC, > nếu ASC.
    Với 1 khoá + id cùng hướng, tương đương (price_vnd, id) < (500000, 42)."""
    branches = []
    for i, (name, desc) in enumerate(keys):
        col = SORTABLE[name]
        same = [SORTABLE[keys[j][0]] == values[j] for j in range(i)]
        branches.append(and_(*same, col < values[i] if desc else col > values[i]))
    return or_(*branches)


@bp.get("/books")
def list_books():
    strategy = request.args.get("strategy", "offset")
    if strategy not in ("offset", "cursor"):
        bad_request("strategy phải là offset hoặc cursor")
    limit = max(1, min(request.args.get("limit", DEFAULT, type=int), MAX_))
    sort = request.args.get("sort", "id")
    keys = parse_sort(sort)

    q = select(Book).options(selectinload(Book.category))   # tránh N+1 khi lấy genre
    genre = request.args.get("genre")
    if genre:   # ?genre=tech hoặc ?genre=tech,novel
        slugs = [g.strip() for g in genre.split(",") if g.strip()]
        q = q.where(Book.category_id.in_(select(Category.id).where(Category.slug.in_(slugs))))
    order = [SORTABLE[n].desc() if d else SORTABLE[n].asc() for n, d in keys]

    if strategy == "offset":
        o = max(0, request.args.get("offset", 0, type=int))
        total = db.session.scalar(select(func.count()).select_from(q.subquery()))
        rows = db.session.scalars(q.order_by(*order).offset(o).limit(limit)).all()
        return jsonify({
            "data": [b.to_dict() for b in rows],
            "pagination": {"offset": o, "limit": limit, "total": total,
                           "has_next": o + limit < total},
        })

    # strategy == "cursor"
    token = request.args.get("cursor")
    if token:
        try:
            c = decode(token)
            values = [date.fromisoformat(v) if n == "published" else v
                      for (n, _), v in zip(keys, c["v"] + [c["i"]])]
        except Exception:
            bad_request("cursor không hợp lệ")
        if c.get("s") != sort or c.get("g") != genre or len(values) != len(keys):
            bad_request("cursor không khớp sort/genre hiện tại, hãy bắt đầu lại từ trang đầu")
        q = q.where(after_cursor(keys, values))
    rows = db.session.scalars(q.order_by(*order).limit(limit + 1)).all()   # +1 trick
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_c = None
    if rows and has_more:
        last = rows[-1].to_dict()
        field = {"title": "title", "price": "price_vnd", "published": "published_at"}
        next_c = encode({"s": sort, "g": genre,
                         "v": [last[field[n]] for n, _ in keys[:-1]], "i": last["id"]})
    return jsonify({
        "data": [b.to_dict() for b in rows],
        "page_info": {"next_cursor": next_c, "has_more": has_more},
    })
