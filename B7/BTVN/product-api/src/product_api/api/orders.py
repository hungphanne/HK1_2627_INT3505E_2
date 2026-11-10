from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from ..errors import NotFound, OutOfStock
from ..extensions import db
from ..models import Order, OrderItem, Product
from ..schemas import OrderIn, OrderOut

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def _eager_items():
    # Order -> items là 1-N: selectinload; OrderItem -> product là to-one: joinedload (slide 16)
    return selectinload(Order.items).joinedload(OrderItem.product)


# POST /api/v1/orders
# body: {"customer_name": "An", "items": [{"product_id": 1, "qty": 2}, ...]}
@orders_bp.post("")
def create_order():
    data = OrderIn().load(request.get_json())
    order = Order(customer_name=data["customer_name"])

    for item in data["items"]:
        p = db.session.get(Product, item["product_id"], with_for_update=True)
        if p is None or p.archived:
            db.session.rollback()
            raise NotFound(f"product {item['product_id']} not found")
        if p.qty_in_stock < item["qty"]:
            db.session.rollback()
            raise OutOfStock(
                f"product {p.id}: requested {item['qty']}, only {p.qty_in_stock} left"
            )
        p.qty_in_stock -= item["qty"]
        order.items.append(
            OrderItem(product=p, qty=item["qty"], unit_price_cents=p.price_cents)
        )

    db.session.add(order)
    db.session.commit()  # 1 commit cho cả đơn: lỗi ở item nào thì không trừ kho item nào
    return OrderOut().dump(order), 201


# GET /api/v1/orders
@orders_bp.get("")
def list_orders():
    rows = db.session.execute(
        select(Order).options(_eager_items()).order_by(Order.id)
    ).scalars().all()
    return jsonify(items=OrderOut(many=True).dump(rows)), 200


# GET /api/v1/orders/<id>
@orders_bp.get("/<int:order_id>")
def get_order(order_id):
    order = db.session.execute(
        select(Order).options(_eager_items()).where(Order.id == order_id)
    ).scalar_one_or_none()
    if order is None:
        raise NotFound(f"order {order_id} not found")
    return OrderOut().dump(order), 200
