from flask import Blueprint, jsonify, request, g
from app.db import db
from app.models.series import Series
from app.models.review import Review
from app.utils import login_required, paginate
from sqlalchemy import func

series_bp = Blueprint("series", __name__, url_prefix="/api/series")


def _serialize_series(s):
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "image_url": s.image_url,
        "rating": s.rating,
        "number_of_seasons": s.number_of_seasons,
        "number_of_episodes": s.number_of_episodes,
        "release_year": s.release_year,
        "genre": s.genre,
        "status": s.status,
        "trailer_url": s.trailer_url
    }


@series_bp.get("/")
def get_all_series():
    query = Series.query.order_by(Series.rating.desc())
    items, meta = paginate(query)
    return jsonify({"items": [_serialize_series(s) for s in items], **meta})


@series_bp.get("/search")
def search_series():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()

    if not q and not genre:
        return jsonify({"error": "Arama parametresi gerekli (?q=... veya ?genre=...)"}), 400

    query = Series.query

    if q:
        query = query.filter(
            Series.title.ilike(f"%{q}%") | Series.description.ilike(f"%{q}%")
        )

    if genre:
        query = query.filter(Series.genre.ilike(f"%{genre}%"))

    query = query.order_by(Series.rating.desc())
    items, meta = paginate(query)
    return jsonify({"items": [_serialize_series(s) for s in items], **meta})


@series_bp.get("/<int:series_id>")
def get_series_detail(series_id):
    s = Series.query.get_or_404(series_id)
    return jsonify(_serialize_series(s))


@series_bp.post("/<int:series_id>/rate")
@login_required
def rate_series(series_id):
    s = Series.query.get_or_404(series_id)
    data = request.get_json(silent=True)

    if not data or "rating" not in data:
        return jsonify({"error": "Puan değeri gerekli."}), 400

    try:
        rating_value = float(data["rating"])
    except (ValueError, TypeError):
        return jsonify({"error": "Geçersiz puan değeri."}), 400

    if not (1.0 <= rating_value <= 10.0):
        return jsonify({"error": "Puan 1 ile 10 arasında olmalıdır."}), 400

    user = g.current_user
    review = Review.query.filter_by(user_id=user.id, series_id=series_id).first()

    if review:
        review.rating = rating_value
    else:
        review = Review(user_id=user.id, series_id=series_id, rating=rating_value)
        db.session.add(review)

    db.session.flush()

    avg = db.session.query(func.avg(Review.rating)).filter_by(series_id=series_id).scalar()
    if avg is not None:
        s.rating = round(float(avg), 1)

    db.session.commit()

    return jsonify({"message": "Puan kaydedildi.", "new_average": s.rating})


@series_bp.get("/<int:series_id>/comments")
def get_comments(series_id):
    Series.query.get_or_404(series_id)

    query = Review.query.filter(
        Review.series_id == series_id,
        Review.comment.isnot(None),
        Review.comment != ""
    ).order_by(Review.created_at.desc())

    items, meta = paginate(query)

    return jsonify({
        "items": [
            {
                "id": r.id,
                "email": r.user.email,
                "text": r.comment,
                "rating": r.rating,
                "created_at": r.created_at.isoformat()
            }
            for r in items
        ],
        **meta
    })


@series_bp.post("/<int:series_id>/comments")
@login_required
def add_comment(series_id):
    Series.query.get_or_404(series_id)
    data = request.get_json(silent=True)

    if not data or not data.get("text", "").strip():
        return jsonify({"error": "Yorum metni boş olamaz."}), 400

    user = g.current_user
    review = Review.query.filter_by(user_id=user.id, series_id=series_id).first()

    if review:
        review.comment = data["text"].strip()
    else:
        review = Review(
            user_id=user.id,
            series_id=series_id,
            rating=5.0,
            comment=data["text"].strip()
        )
        db.session.add(review)

    db.session.commit()

    return jsonify({
        "id": review.id,
        "email": user.email,
        "text": review.comment,
        "created_at": review.created_at.isoformat()
    }), 201
