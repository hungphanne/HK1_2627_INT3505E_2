# Tên hàm phải trùng operationId trong openapi/products.yaml.
# Body và path param đã được connexion validate theo spec trước khi vào đây.
from sqlalchemy.exc import IntegrityError

from models import Product, db


def list_products():
    rows = db.session.execute(db.select(Product).order_by(Product.id)).scalars().all()
    return [p.to_dict() for p in rows], 200


def create_product(body):
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"detail": "sku already exists"}, 409
    return p.to_dict(), 201


def get_product(id):
    p = db.session.get(Product, id)
    if p is None:
        return {"detail": f"product {id} not found"}, 404
    return p.to_dict(), 200
