# REVIEW ROUTES: Kullanıcı yorumları ve puanlarıyla ilgili tüm API endpoint'leri.

from flask import Blueprint, jsonify, request, session
from app.db import db
from app.models.user import User
from app.models.series import Series
from app.models.review import Review

review_bp = Blueprint("review", __name__, url_prefix="/api/reviews")


def get_current_user():
    """Session'dan giriş yapmış kullanıcıyı döndürür."""
    email = session.get("user")
    if not email:
        return None
    return User.query.filter_by(email=email).first()


# QUERY: Belirli bir diziye ait tüm yorumları getirir (SELECT + JOIN ile kullanıcı bilgisiyle birlikte)
@review_bp.get("/series/<int:series_id>")
def get_reviews_for_series(series_id):
    reviews = Review.query.filter_by(series_id=series_id).all()
    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "user_email": r.user.email,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        })
    return jsonify(result)


# QUERY: Yeni yorum ve puan ekler (INSERT)
@review_bp.post("/add")
def add_review():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    data = request.get_json()
    series_id = data.get("series_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    # Dizi var mı kontrol et
    series = Series.query.get(series_id)
    if not series:
        return jsonify({"error": "Dizi bulunamadı"}), 404

    # Puan geçerli mi kontrol et
    if not rating or not (1.0 <= float(rating) <= 10.0):
        return jsonify({"error": "Puan 1.0 ile 10.0 arasında olmalıdır"}), 400

    # QUERY: Kullanıcının bu diziye daha önce yorum yapıp yapmadığını kontrol eder (SELECT)
    existing = Review.query.filter_by(user_id=user.id, series_id=series_id).first()
    if existing:
        return jsonify({"error": "Bu diziye zaten yorum yaptınız"}), 409

    new_review = Review(
        user_id=user.id,
        series_id=series_id,
        rating=float(rating),
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"message": f"'{series.title}' için yorumunuz eklendi"}), 201


# QUERY: Kullanıcının kendi yorumunu günceller (UPDATE)
@review_bp.put("/update/<int:review_id>")
def update_review(review_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    review = Review.query.filter_by(id=review_id, user_id=user.id).first()
    if not review:
        return jsonify({"error": "Yorum bulunamadı"}), 404

    data = request.get_json()
    new_rating = data.get("rating")
    new_comment = data.get("comment")

    if new_rating:
        if not (1.0 <= float(new_rating) <= 10.0):
            return jsonify({"error": "Puan 1.0 ile 10.0 arasında olmalıdır"}), 400
        review.rating = float(new_rating)

    if new_comment is not None:
        review.comment = new_comment

    db.session.commit()
    return jsonify({"message": "Yorumunuz güncellendi"})


# QUERY: Kullanıcının kendi yorumunu siler (DELETE)
@review_bp.delete("/delete/<int:review_id>")
def delete_review(review_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Giriş yapmalısınız"}), 401

    review = Review.query.filter_by(id=review_id, user_id=user.id).first()
    if not review:
        return jsonify({"error": "Yorum bulunamadı"}), 404

    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Yorumunuz silindi"})
