from datetime import date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)   # genre: tech, novel...


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False, default=0)
    published_at = db.Column(db.Date, nullable=False, default=date(2000, 1, 1))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship(Category)

    # index (sort key, id) cho keyset pagination
    __table_args__ = (db.Index("ix_books_price_id", "price_vnd", "id"),)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.category.slug if self.category else None,
            "price_vnd": self.price_vnd,
            "published_at": self.published_at.isoformat(),
        }
