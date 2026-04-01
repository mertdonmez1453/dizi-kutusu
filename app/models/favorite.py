from datetime import datetime
from app.db import db

# MODEL: Kullanıcıların favori dizilerini tuttuğu tablo.
# Her satır bir kullanıcı-dizi favori eşleşmesidir.
class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler — Kullanıcı ve dizi bilgilerine kolay erişim sağlar
    user = db.relationship("User", backref=db.backref("favorites", lazy=True))
    series = db.relationship("Series", backref=db.backref("favorites", lazy=True))

    # Aynı kullanıcı aynı diziyi iki kez favoriye ekleyemesin
    __table_args__ = (
        db.UniqueConstraint("user_id", "series_id", name="uq_user_series_favorite"),
    )
