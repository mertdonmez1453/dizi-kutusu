from app.db import db

# MODEL: Dizilerin bölüm bilgilerini tutan tablo.
# Her satır bir dizinin bir bölümünü temsil eder (sezon ve bölüm numarası ile).
class Episode(db.Model):
    __tablename__ = "episodes"

    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    season_number = db.Column(db.Integer, nullable=False)   # Sezon numarası
    episode_number = db.Column(db.Integer, nullable=False)   # Bölüm numarası
    title = db.Column(db.String(200), nullable=True)         # Bölüm adı
    air_date = db.Column(db.Date, nullable=True)             # Yayın tarihi

    # İlişki — Hangi diziye ait olduğuna kolay erişim sağlar
    series = db.relationship("Series", backref=db.backref("episodes", lazy=True))

    # Aynı dizide aynı sezon-bölüm kombinasyonu tekrar edemez
    __table_args__ = (
        db.UniqueConstraint("series_id", "season_number", "episode_number", name="uq_series_season_episode"),
    )
