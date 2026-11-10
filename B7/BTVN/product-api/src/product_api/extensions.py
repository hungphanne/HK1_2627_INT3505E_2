from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Khai báo ở module-level, CHƯA gắn app. Factory sẽ gọi init_app(app).
db = SQLAlchemy()
migrate = Migrate()
