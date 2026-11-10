from marshmallow import Schema, fields, validate


# Schema output — flask-smorest dùng để serialize response VÀ sinh OpenAPI
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str()
    name = fields.Str()
    price_cents = fields.Int()


# Schema input — flask-smorest dùng để validate body (sai -> 422) VÀ sinh OpenAPI
class ProductInSchema(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
