from flask import Blueprint, jsonify, request, g
from app.db import db
from app.models.user import User
from app.models.series import Series
from app.models.review import Review
from app.models.watchlist import Watchlist
from app.utils import admin_required, paginate

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/stats")
@admin_required
def get_stats():
    return jsonify({
        "total_users": User.query.count(),
        "total_series": Series.query.count(),
        "total_reviews": Review.query.count(),
        "total_watchlist": Watchlist.query.count()
    })


@admin_bp.get("/users")
@admin_required
def get_users():
    def _serialize_user(u):
        return {
            "id": u.id,
            "email": u.email,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat()
        }

    query = User.query.order_by(User.id)
    return paginate(query, _serialize_user)


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    if g.current_user.id == user_id:
        return jsonify({"error": "Kendi hesabınızı silemezsiniz."}), 400

    user = User.query.get_or_404(user_id)

    Watchlist.query.filter_by(user_id=user_id).delete()
    Review.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"'{user.email}' kullanıcısı silindi."})


@admin_bp.post("/series")
@admin_required
def create_series():
    data = request.get_json(silent=True)
    if not data or not data.get("title", "").strip():
        return jsonify({"error": "Dizi başlığı zorunludur."}), 400

    if Series.query.filter_by(title=data["title"].strip()).first():
        return jsonify({"error": "Bu isimde bir dizi zaten mevcut."}), 409

    new_series = Series(
        title=data["title"].strip(),
        description=data.get("description", "").strip() or "Açıklama bulunmuyor.",
        genre=data.get("genre"),
        release_year=data.get("release_year"),
        rating=data.get("rating"),
        number_of_seasons=data.get("number_of_seasons"),
        number_of_episodes=data.get("number_of_episodes"),
        status=data.get("status"),
        image_url=data.get("image_url"),
        trailer_url=data.get("trailer_url")
    )
    db.session.add(new_series)
    db.session.commit()

    return jsonify({"message": f"'{new_series.title}' eklendi.", "id": new_series.id}), 201


@admin_bp.put("/series/<int:series_id>")
@admin_required
def update_series(series_id):
    s = Series.query.get_or_404(series_id)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    if "title" in data and data["title"]:
        s.title = data["title"].strip()
    if "description" in data:
        s.description = data["description"].strip() or s.description
    if "genre" in data:
        s.genre = data["genre"]
    if "release_year" in data:
        s.release_year = data["release_year"]
    if "rating" in data:
        s.rating = data["rating"]
    if "number_of_seasons" in data:
        s.number_of_seasons = data["number_of_seasons"]
    if "number_of_episodes" in data:
        s.number_of_episodes = data["number_of_episodes"]
    if "status" in data:
        s.status = data["status"]
    if "image_url" in data:
        s.image_url = data["image_url"]
    if "trailer_url" in data:
        s.trailer_url = data["trailer_url"]

    db.session.commit()

    return jsonify({"message": f"'{s.title}' güncellendi."})


@admin_bp.delete("/series/<int:series_id>")
@admin_required
def delete_series(series_id):
    s = Series.query.get_or_404(series_id)

    Watchlist.query.filter_by(series_id=series_id).delete()
    Review.query.filter_by(series_id=series_id).delete()

    db.session.delete(s)
    db.session.commit()

    return jsonify({"message": f"'{s.title}' silindi."})


@admin_bp.get("/reviews")
@admin_required
def get_reviews():
    def _serialize_review(r):
        return {
            "id": r.id,
            "email": r.user.email,
            "series_title": r.series.title,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        }

    query = Review.query.order_by(Review.created_at.desc())
    return paginate(query, _serialize_review)


@admin_bp.delete("/reviews/<int:review_id>")
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Yorum silindi."})
