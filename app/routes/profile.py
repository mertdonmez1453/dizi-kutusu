import re
from flask import Blueprint, request, jsonify, g, session
from app.db import db
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.friendship import Friendship
from app.utils import login_required

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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
        "username": user.username,
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


@profile_bp.post("/api/settings/email")
@login_required
def update_email():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    new_email = data.get("new_email", "").strip()
    password = data.get("password", "")

    if not new_email or not password:
        return jsonify({"error": "Yeni e-posta ve şifre alanları zorunludur."}), 400

    if not EMAIL_REGEX.match(new_email):
        return jsonify({"error": "Geçerli bir e-posta adresi giriniz."}), 400

    user = g.current_user

    if not user.check_password(password):
        return jsonify({"error": "Şifre hatalı."}), 403

    if new_email == user.email:
        return jsonify({"error": "Yeni e-posta mevcut e-postanızla aynı."}), 400

    if User.query.filter_by(email=new_email).first():
        return jsonify({"error": "Bu e-posta adresi zaten kullanılıyor."}), 409

    user.email = new_email
    session["user"] = new_email
    db.session.commit()

    return jsonify({"message": "E-posta başarıyla güncellendi.", "email": new_email})


@profile_bp.delete("/api/settings/account")
@login_required
def delete_account():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    password = data.get("password", "")
    if not password:
        return jsonify({"error": "Hesabı silmek için şifrenizi girmelisiniz."}), 400

    user = g.current_user

    if not user.check_password(password):
        return jsonify({"error": "Şifre hatalı."}), 403

    Review.query.filter_by(user_id=user.id).delete()
    Watchlist.query.filter_by(user_id=user.id).delete()
    Favorite.query.filter_by(user_id=user.id).delete()
    Friendship.query.filter_by(follower_id=user.id).delete()
    Friendship.query.filter_by(followed_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

    session.clear()

    return jsonify({"message": "Hesabınız başarıyla silindi."})
