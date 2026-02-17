from flask import Flask

def create_app():
    app = Flask(__name__)

    # session/flash için gerekli (giriş yaptı bilgisini tutacağız)
    app.config["SECRET_KEY"] = "dev-secret-key"

    # Blueprints
    from .routes.health import health_bp
    app.register_blueprint(health_bp)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    return app