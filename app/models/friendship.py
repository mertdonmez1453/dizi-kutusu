from datetime import datetime
from app.db import db

# MODEL: Kullanıcıların birbirini takip etmesi / arkadaş olması için kullanılan tablo.
# Çoktan çoğa (Many-to-Many) ilişkiyi temsil eder.
class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    
    # Takip eden kullanıcı
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Takip edilen kullanıcı
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Ne zaman takip etmeye başladı
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # İlişkiler
    # (Kullanıcı modelinde backref ile followers ve following listelerine erişilebilir)
    follower = db.relationship("User", foreign_keys=[follower_id], backref=db.backref("following", lazy="dynamic"))
    followed = db.relationship("User", foreign_keys=[followed_id], backref=db.backref("followers", lazy="dynamic"))

    # Bir kullanıcı başka bir kullanıcıyı sadece bir kez takip edebilir
    __table_args__ = (
        db.UniqueConstraint("follower_id", "followed_id", name="uq_follower_followed"),
    )
