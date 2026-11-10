from flask import Blueprint, jsonify, request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from ..errors import Conflict, NotFound, OutOfStock
from ..extensions import db
from ..models import Product
from ..schemas import ProductIn, ProductOut, ProductPatch, ReserveIn

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def _get_active_or_404(product_id):
    """db.get_or_404 không loại sản phẩm archived, nên tự viết."""
    p = db.session.get(Product, product_id)
    if p is None or p.archived:
        raise NotFound(f"product {product_id} not found")
    return p


# GET /api/v1/products?page=1&size=20
@products_bp.get("")
def list_products():
    page = max(1, request.args.get("page", 1, type=int))
    size = min(100, max(1, request.args.get("size", 20, type=int)))

    active = Product.archived.is_(False)
    rows = db.session.execute(
        select(Product).where(active).order_by(Product.id)
        .offset((page - 1) * size).limit(size)
    ).scalars().all()
    total = db.session.scalar(select(func.count()).select_from(Product).where(active))

    return jsonify(
        items=ProductOut(many=True).dump(rows), page=page, size=size, total=total
    ), 200


# GET /api/v1/products/<id>
@products_bp.get("/<int:product_id>")
def get_product(product_id):
    return ProductOut().dump(_get_active_or_404(product_id)), 200


# POST /api/v1/products
@products_bp.post("")
def create_product():
    data = ProductIn().load(request.get_json())
    p = Product(**data)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(f"sku '{data['sku']}' already exists")
    return ProductOut().dump(p), 201


# POST /api/v1/products/<id>/reserve   body: {"qty": 1}
@products_bp.post("/<int:product_id>/reserve")
def reserve_product(product_id):
    qty = ReserveIn().load(request.get_json())["qty"]
    p = _get_active_or_404(product_id)
    available = p.qty_in_stock

    # UPDATE có điều kiện => kiểm tra và trừ kho trong 1 câu SQL (atomic).
    # Hai request đồng thời không thể cùng trừ làm tồn kho < 0.
    result = db.session.execute(
        update(Product)
        .where(Product.id == product_id, Product.qty_in_stock >= qty)
        .values(qty_in_stock=Product.qty_in_stock - qty)
    )
    if result.rowcount == 0:
        db.session.rollback()
        raise OutOfStock(f"requested {qty}, only {available} left")

    db.session.commit()
    db.session.refresh(p)
    return ProductOut().dump(p), 200


# PATCH /api/v1/products/<id>
@products_bp.patch("/<int:product_id>")
def patch_product(product_id):
    data = ProductPatch().load(request.get_json(), partial=True)
    p = _get_active_or_404(product_id)
    for key, value in data.items():  # chỉ field có trong body mới đổi
        setattr(p, key, value)
    db.session.commit()
    return ProductOut().dump(p), 200


# DELETE /api/v1/products/<id>  -> soft delete
@products_bp.delete("/<int:product_id>")
def delete_product(product_id):
    p = _get_active_or_404(product_id)
    p.archived = True
    db.session.commit()
    return "", 204
