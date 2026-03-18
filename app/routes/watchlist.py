# WATCHLIST ROUTES: Kullanıcının izleme listesiyle ilgili tüm API endpoint'leri burada tanımlanır.

from flask import Blueprint, jsonify, request, session
from app.db import db
from app.models.user import User
from app.models.series import Series
from app.models.watchlist import Watchlist

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


def get_current_user():
    """Session'dan giriş yapmış kullanıcıyı döndürür."""
    email = session.get("user")
    if not email:
        return None
    return User.query.filter_by(email=email).first()


# QUERY: Kullanıcının izleme listesindeki tüm dizileri getirir (SELECT + JOIN)
@watchlist_bp.get("/")
def get_watchlist():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    items = Watchlist.query.filter_by(user_id=user.id).all()
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
            "status": item.status,
            "added_at": item.added_at.isoformat()
        })
    return jsonify(result)


# QUERY: İzleme listesine yeni dizi ekler (INSERT)
@watchlist_bp.post("/add")
def add_to_watchlist():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    data = request.get_json()
    series_id = data.get("series_id")
    status = data.get("status", "plan_to_watch")

    # Dizi var mı kontrol et
    series = Series.query.get(series_id)
    if not series:
        return jsonify({"error": "Dizi bulunamadı"}), 404

    # Zaten listede mi kontrol et
    existing = Watchlist.query.filter_by(user_id=user.id, series_id=series_id).first()
    if existing:
        return jsonify({"error": "Bu dizi zaten listenizde"}), 409

    new_item = Watchlist(user_id=user.id, series_id=series_id, status=status)
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": f"'{series.title}' izleme listesine eklendi"}), 201


# QUERY: İzleme listesindeki bir dizinin durumunu günceller (UPDATE)
@watchlist_bp.put("/update/<int:item_id>")
def update_watchlist_status(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    item = Watchlist.query.filter_by(id=item_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "Kayıt bulunamadı"}), 404

    data = request.get_json()
    new_status = data.get("status")

    valid_statuses = ["watching", "completed", "plan_to_watch", "dropped"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Geçersiz durum. Geçerli değerler: {valid_statuses}"}), 400

    item.status = new_status
    db.session.commit()

    return jsonify({"message": f"Durum '{new_status}' olarak güncellendi"})


# QUERY: İzleme listesinden bir diziyi siler (DELETE)
@watchlist_bp.delete("/remove/<int:item_id>")
def remove_from_watchlist(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    item = Watchlist.query.filter_by(id=item_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "Kayıt bulunamadı"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Dizi izleme listesinden kaldırıldı"})
