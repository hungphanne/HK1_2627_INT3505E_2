from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "sku": self.sku, "name": self.name, "price_cents": self.price_cents}
