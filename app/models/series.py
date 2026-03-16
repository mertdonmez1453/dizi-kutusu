from datetime import datetime
from app.db import db

class Series(db.Model):
    __tablename__ = "series"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    number_of_seasons = db.Column(db.Integer, nullable=True)
    number_of_episodes = db.Column(db.Integer, nullable=True)
    release_year = db.Column(db.Integer)
    genre = db.Column(db.String(100), nullable=True)
    trailer_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  

