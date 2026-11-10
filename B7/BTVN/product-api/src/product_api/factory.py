import os

from flask import Flask

from . import models  # noqa: F401  — import để Flask-Migrate/Alembic "thấy" các model
from .config import DefaultConfig
from .errors import register_error_handlers
from .extensions import db, migrate


def create_app(config=None):
    app = Flask(__name__)
    # config có thể là class (TestConfig) hoặc chuỗi "product_api.config.ProductionConfig"
    app.config.from_object(config or os.environ.get("APP_CONFIG", DefaultConfig))

    db.init_app(app)
    migrate.init_app(app, db)
    register_error_handlers(app)

    from .api.health import health_bp
    from .api.orders import orders_bp
    from .api.products import products_bp

    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(health_bp)
    return app
