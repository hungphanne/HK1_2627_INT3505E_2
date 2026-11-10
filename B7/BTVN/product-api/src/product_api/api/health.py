from flask import Blueprint, jsonify
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__)


# Liveness — "process còn sống không?" — KHÔNG chạm DB
@health_bp.get("/healthz")
def liveness():
    return jsonify(status="ok"), 200


# Readiness — "nhận traffic được chưa?" — kiểm tra dependency (DB)
@health_bp.get("/ready")
def readiness():
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        db.session.rollback()
        checks["db"] = "error"
    ok = all(v == "ok" for v in checks.values())
    return jsonify(status="ok" if ok else "degraded", checks=checks), (200 if ok else 503)
