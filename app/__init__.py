import click
from flask import Flask
from app.db import db

def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = True

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.models import User, Series, Watchlist, Review, Favorite, Episode, Friendship

    from .routes.health import health_bp
    app.register_blueprint(health_bp)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    from .routes.profile import profile_bp
    app.register_blueprint(profile_bp)

    from .routes.series import series_bp
    app.register_blueprint(series_bp)

    from .routes.watchlist import watchlist_bp
    app.register_blueprint(watchlist_bp)

    from .routes.review import review_bp
    app.register_blueprint(review_bp)

    from .routes.favorite import favorite_bp
    app.register_blueprint(favorite_bp)

    from .routes.episode import episode_bp
    app.register_blueprint(episode_bp)

    from .routes.friendship import friendship_bp
    app.register_blueprint(friendship_bp)

    from .routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    @app.cli.command("set-admin")
    @click.argument("email")
    def set_admin(email):
        """Belirtilen e-posta adresine sahip kullanıcıyı admin yapar."""
        user = User.query.filter_by(email=email).first()
        if user is None:
            click.echo(f"Hata: '{email}' ile kayıtlı kullanıcı bulunamadı.")
            return
        user.is_admin = True
        db.session.commit()
        click.echo(f"'{email}' artık admin.")

    with app.app_context():
        db.create_all()

    return app
