# FAVORITE ROUTES: Kullanıcıların favori dizileriyle ilgili tüm API endpoint'leri.

from flask import Blueprint, jsonify, request, session
from app.db import db
from app.models.user import User
from app.models.series import Series
from app.models.favorite import Favorite

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/favorites")


def get_current_user():
    """Session'dan giriş yapmış kullanıcıyı döndürür."""
    email = session.get("user")
    if not email:
        return None
    return User.query.filter_by(email=email).first()


# QUERY: Kullanıcının favori dizilerini getirir (SELECT + JOIN)
@favorite_bp.get("/")
def get_favorites():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    items = Favorite.query.filter_by(user_id=user.id).all()
    result = []
    for item in items:
        s = item.series
        result.append({
            "id": item.id,
            "series_id": s.id,
            "title": s.title,
            "image_url": s.image_url,
            "rating": s.rating,
            "genre": s.genre,
            "added_at": item.added_at.isoformat()
        })
    return jsonify(result)


# QUERY: Favorilere yeni dizi ekler (INSERT)
@favorite_bp.post("/add")
def add_to_favorites():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    data = request.get_json()
    series_id = data.get("series_id")

    # QUERY: Dizinin veritabanında var olup olmadığını kontrol eder (SELECT)
    series = Series.query.get(series_id)
    if not series:
        return jsonify({"error": "Dizi bulunamadı"}), 404

    # QUERY: Kullanıcının bu diziyi daha önce favoriye ekleyip eklemediğini kontrol eder (SELECT)
    existing = Favorite.query.filter_by(user_id=user.id, series_id=series_id).first()
    if existing:
        return jsonify({"error": "Bu dizi zaten favorilerinizde"}), 409

    new_fav = Favorite(user_id=user.id, series_id=series_id)
    db.session.add(new_fav)
    db.session.commit()

    return jsonify({"message": f"'{series.title}' favorilere eklendi"}), 201


# QUERY: Favorilerden bir diziyi kaldırır (DELETE)
@favorite_bp.delete("/remove/<int:item_id>")
def remove_from_favorites(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    # QUERY: Kullanıcının bu favori kaydının var olup olmadığını kontrol eder (SELECT)
    item = Favorite.query.filter_by(id=item_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "Kayıt bulunamadı"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Dizi favorilerden kaldırıldı"})
