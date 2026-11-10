import connexion

from models import db

# connexion đọc spec và tự tạo Flask route cho từng operationId
app = connexion.FlaskApp(__name__, specification_dir="openapi/")
app.add_api("products.yaml", validate_responses=True)

# Flask app bên trong — dùng để gắn Flask-SQLAlchemy
flask_app = app.app
flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
db.init_app(flask_app)
with flask_app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(port=8080)
