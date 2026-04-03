from datetime import datetime
from app.db import db

# MODEL: Kullanıcıların dizilere yorum ve puan verdiği tablo.
# Her satır bir kullanıcı-dizi yorumunu temsil eder.
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    rating = db.Column(db.Float, nullable=False)  # 1.0 - 10.0 arası puan
    comment = db.Column(db.Text, nullable=True)    # Yorum metni
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler — Kullanıcı ve dizi bilgilerine kolay erişim sağlar
    user = db.relationship("User", backref=db.backref("reviews", lazy=True))
    series = db.relationship("Series", backref=db.backref("reviews", lazy=True))

    # Bir kullanıcı aynı diziye birden fazla yorum yapamamalı
    __table_args__ = (
        db.UniqueConstraint("user_id", "series_id", name="uq_user_series_review"),
    )
