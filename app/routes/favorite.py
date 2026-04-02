from flask import Blueprint, jsonify, g
from app.db import db
from app.models.series import Series
from app.models.favorite import Favorite
from app.utils import login_required

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/favorites")


# QUERY: Kullanıcının favori dizilerini getirir (SELECT + JOIN)
@favorite_bp.get("/")
@login_required
def get_favorites():
    user = g.current_user
    items = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.added_at.desc()).all()

    return jsonify([
        {
            "id": item.id,
            "series_id": item.series.id,
            "title": item.series.title,
            "image_url": item.series.image_url,
            "rating": item.series.rating,
            "genre": item.series.genre,
            "added_at": item.added_at.isoformat()
        }
        for item in items
    ])


# QUERY: Bir dizinin favorilerde olup olmadığını kontrol eder (SELECT)
@favorite_bp.get("/<int:series_id>")
@login_required
def check_favorite(series_id):
    user = g.current_user
    item = Favorite.query.filter_by(user_id=user.id, series_id=series_id).first()
    return jsonify({"is_favorite": item is not None})


# QUERY: Favorilere yeni dizi ekler (INSERT)
@favorite_bp.post("/<int:series_id>")
@login_required
def add_favorite(series_id):
    Series.query.get_or_404(series_id)
    user = g.current_user

    existing = Favorite.query.filter_by(user_id=user.id, series_id=series_id).first()
    if existing:
        return jsonify({"error": "Bu dizi zaten favorilerinizde."}), 409

    new_fav = Favorite(user_id=user.id, series_id=series_id)
    db.session.add(new_fav)
    db.session.commit()

    return jsonify({"message": "Favorilere eklendi."}), 201


# QUERY: Favorilerden bir diziyi kaldırır (DELETE)
@favorite_bp.delete("/<int:series_id>")
@login_required
def remove_favorite(series_id):
    user = g.current_user
    item = Favorite.query.filter_by(user_id=user.id, series_id=series_id).first()
    if not item:
        return jsonify({"error": "Bu dizi favorilerinizde değil."}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Favorilerden kaldırıldı."})
