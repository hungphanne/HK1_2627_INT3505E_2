from marshmallow import Schema, ValidationError, fields, validate, validates_schema


# ─── Product ──────────────────────────────────────────────
class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))


class ProductPatch(Schema):
    # Không có sku: sku là định danh nghiệp vụ, không cho đổi qua PATCH
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(validate=validate.Range(min=0))
    qty_in_stock = fields.Int(validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


# ─── Order ────────────────────────────────────────────────
class OrderItemIn(Schema):
    product_id = fields.Int(required=True)
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    customer_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    items = fields.List(
        fields.Nested(OrderItemIn), required=True, validate=validate.Length(min=1)
    )

    @validates_schema
    def _no_duplicate_product(self, data, **kwargs):
        ids = [item["product_id"] for item in data.get("items", [])]
        if len(ids) != len(set(ids)):
            raise ValidationError("each product_id may appear only once", "items")


class OrderItemOut(Schema):
    id = fields.Int()
    qty = fields.Int()
    unit_price_cents = fields.Int()
    product = fields.Nested(ProductOut(only=("id", "sku", "name")))


class OrderOut(Schema):
    id = fields.Int()
    customer_name = fields.Str()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOut))
