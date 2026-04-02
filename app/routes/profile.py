from flask import Blueprint, request, jsonify, g
from app.db import db
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.review import Review
from app.utils import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/api/profile")
@login_required
def get_profile():
    user = g.current_user

    watchlist_items = Watchlist.query.filter_by(user_id=user.id).all()
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).limit(5).all()

    status_counts = {"watching": 0, "completed": 0, "plan_to_watch": 0, "dropped": 0}
    for item in watchlist_items:
        if item.status in status_counts:
            status_counts[item.status] += 1

    recent_activity = []
    for r in reviews:
        activity = {
            "series_id": r.series_id,
            "series_title": r.series.title,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        }
        recent_activity.append(activity)

    return jsonify({
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "stats": {
            "total_watchlist": len(watchlist_items),
            "watching": status_counts["watching"],
            "completed": status_counts["completed"],
            "plan_to_watch": status_counts["plan_to_watch"],
            "dropped": status_counts["dropped"],
            "total_reviews": Review.query.filter_by(user_id=user.id).count()
        },
        "recent_activity": recent_activity
    })


@profile_bp.get("/api/profile/reviews")
@login_required
def get_user_reviews():
    user = g.current_user
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.created_at.desc()).all()

    return jsonify([
        {
            "id": r.id,
            "series_id": r.series_id,
            "series_title": r.series.title,
            "series_image": r.series.image_url,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        }
        for r in reviews
    ])


@profile_bp.post("/api/settings/password")
@login_required
def update_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Mevcut şifre ve yeni şifre alanları zorunludur."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Yeni şifre en az 6 karakter olmalıdır."}), 400

    user = g.current_user

    if not user.check_password(current_password):
        return jsonify({"error": "Mevcut şifre hatalı."}), 403

    user.password_hash = User.hash_password(new_password)
    db.session.commit()

    return jsonify({"message": "Şifre başarıyla güncellendi."})
