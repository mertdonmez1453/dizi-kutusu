from flask import Flask
from app.db import db

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .routes.health import health_bp
    app.register_blueprint(health_bp)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
