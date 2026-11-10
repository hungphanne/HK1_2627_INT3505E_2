from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Product
from schemas import ProductInSchema, ProductSchema

blp = Blueprint("products", __name__, url_prefix="/products", description="Product API")


@blp.route("")
class ProductList(MethodView):
    @blp.response(200, ProductSchema(many=True))
    def get(self):
        return db.session.execute(db.select(Product).order_by(Product.id)).scalars().all()

    @blp.arguments(ProductInSchema)  # validate POST body
    @blp.response(201, ProductSchema)
    def post(self, data):
        p = Product(**data)
        db.session.add(p)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="sku already exists")
        return p


@blp.route("/<int:product_id>")
class ProductById(MethodView):
    @blp.response(200, ProductSchema)
    def get(self, product_id):
        p = db.session.get(Product, product_id)
        if p is None:
            abort(404, message="product not found")
        return p
