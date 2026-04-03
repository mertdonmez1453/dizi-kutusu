# WATCHLIST ROUTES: Kullanıcının izleme listesiyle ilgili tüm API endpoint'leri burada tanımlanır.

from flask import Blueprint, jsonify, request, session, g
from app.db import db
from app.models.user import User
from app.models.series import Series
from app.models.watchlist import Watchlist
from app.utils import login_required

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


# ── Frontend-uyumlu endpoint'ler (series_id bazlı) ──

@watchlist_bp.get("/<int:series_id>")
@login_required
def check_watchlist(series_id):
    user = g.current_user
    item = Watchlist.query.filter_by(user_id=user.id, series_id=series_id).first()
    return jsonify({
        "in_watchlist": item is not None,
        "status": item.status if item else None
    })


@watchlist_bp.post("/<int:series_id>")
@login_required
def add_to_watchlist_by_series(series_id):
    Series.query.get_or_404(series_id)
    user = g.current_user

    existing = Watchlist.query.filter_by(user_id=user.id, series_id=series_id).first()
    if existing:
        return jsonify({"error": "Bu dizi zaten listenizde."}), 409

    new_item = Watchlist(user_id=user.id, series_id=series_id, status="plan_to_watch")
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "İzleme listesine eklendi."}), 201


@watchlist_bp.put("/<int:series_id>/status")
@login_required
def update_status_by_series(series_id):
    user = g.current_user
    item = Watchlist.query.filter_by(user_id=user.id, series_id=series_id).first()

    if not item:
        return jsonify({"error": "Bu dizi listenizde değil."}), 404

    data = request.get_json(silent=True)
    if not data or "status" not in data:
        return jsonify({"error": "Durum değeri gerekli."}), 400

    valid_statuses = ["watching", "completed", "plan_to_watch", "dropped"]
    new_status = data["status"]

    if new_status not in valid_statuses:
        return jsonify({"error": f"Geçersiz durum. Geçerli değerler: {valid_statuses}"}), 400

    item.status = new_status
    db.session.commit()

    return jsonify({"message": f"Durum '{new_status}' olarak güncellendi.", "status": new_status})


@watchlist_bp.delete("/<int:series_id>")
@login_required
def remove_from_watchlist_by_series(series_id):
    user = g.current_user
    item = Watchlist.query.filter_by(user_id=user.id, series_id=series_id).first()

    if not item:
        return jsonify({"error": "Bu dizi listenizde değil."}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "İzleme listesinden kaldırıldı."})
