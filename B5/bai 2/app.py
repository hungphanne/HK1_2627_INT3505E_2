import random
from datetime import date, timedelta

from flask import Flask

from models import Book, Category, db
from routes.books import bp


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    app.config.update(config or {})
    db.init_app(app)
    app.register_blueprint(bp, url_prefix="/api/v1")

    @app.cli.command("init-db")
    def init_db():
        """Tạo lại bảng và nạp dữ liệu mẫu."""
        db.drop_all()
        db.create_all()
        seed()
        print("Database ready.")

    return app


def seed(n_books=60):
    """Dữ liệu mẫu: giá cố ý trùng nhiều để kiểm tra tie-break của cursor."""
    rnd = random.Random(42)
    cats = [Category(name=n, slug=s) for n, s in
            [("Công nghệ", "tech"), ("Tiểu thuyết", "novel"), ("Khoa học", "science"), ("Lịch sử", "history")]]
    db.session.add_all(cats)
    for i in range(1, n_books + 1):
        db.session.add(Book(
            title=f"Book {rnd.choice('ABCDEFGH')}{i:02d}",
            price_vnd=rnd.choice([89_000, 150_000, 250_000, 450_000]),
            published_at=date(2000, 1, 1) + timedelta(days=rnd.randrange(8000)),
            category=rnd.choice(cats),
        ))
    db.session.commit()

