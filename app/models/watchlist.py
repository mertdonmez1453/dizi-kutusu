from datetime import datetime
from app.db import db

# MODEL: Kullanıcının izleme listesini tutan tablo. Her satır bir kullanıcı-dizi eşleşmesidir.
class Watchlist(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="plan_to_watch")
    # status değerleri: "watching", "completed", "plan_to_watch", "dropped"
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler (relationship) — Kullanıcı ve dizi bilgilerine kolay erişim sağlar
    user = db.relationship("User", backref=db.backref("watchlist", lazy=True))
    series = db.relationship("Series", backref=db.backref("watchlist", lazy=True))

    # Aynı kullanıcı aynı diziyi iki kez ekleyemesin
    __table_args__ = (
        db.UniqueConstraint("user_id", "series_id", name="uq_user_series"),
    )
