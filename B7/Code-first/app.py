from flask import Flask
from flask_smorest import Api

from extensions import db
from products import blp


def create_app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///products.db",
        # Cấu hình bắt buộc để flask-smorest sinh OpenAPI + Swagger UI
        API_TITLE="Product API (code-first)",
        API_VERSION="1.0.0",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json",
        OPENAPI_SWAGGER_UI_PATH="/swagger-ui",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )
    db.init_app(app)
    api = Api(app)
    api.register_blueprint(blp)

    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
