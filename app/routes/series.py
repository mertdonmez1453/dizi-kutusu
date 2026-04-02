from flask import Blueprint, jsonify, request, g, session
from app.db import db
from app.models.series import Series
from app.models.review import Review
from app.models.watchlist import Watchlist
from app.models.user import User
from app.utils import login_required, paginate
from sqlalchemy import func
from sqlalchemy.sql.expression import func as sql_func

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
    return paginate(query, _serialize_series)


@series_bp.get("/search")
def search_series():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    year = request.args.get("year", type=int)
    min_rating = request.args.get("min_rating", type=float)
    max_rating = request.args.get("max_rating", type=float)
    status = request.args.get("status", "").strip()
    sort_by = request.args.get("sort_by", "rating").strip()

    if not q and not genre and not year and min_rating is None and not status:
        return jsonify({"error": "En az bir arama/filtre parametresi gerekli."}), 400

    query = Series.query

    if q:
        query = query.filter(
            Series.title.ilike(f"%{q}%") | Series.description.ilike(f"%{q}%")
        )

    if genre:
        query = query.filter(Series.genre.ilike(f"%{genre}%"))

    if year:
        query = query.filter(Series.release_year == year)

    if min_rating is not None:
        query = query.filter(Series.rating >= min_rating)

    if max_rating is not None:
        query = query.filter(Series.rating <= max_rating)

    if status:
        query = query.filter(Series.status.ilike(f"%{status}%"))

    sort_options = {
        "rating": Series.rating.desc(),
        "year": Series.release_year.desc(),
        "title": Series.title.asc(),
    }
    query = query.order_by(sort_options.get(sort_by, Series.rating.desc()))

    return paginate(query, _serialize_series)


@series_bp.get("/random")
def random_series():
    genre = request.args.get("genre", "").strip()

    query = Series.query

    email = session.get("user")
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            watched_ids = db.session.query(Watchlist.series_id).filter_by(user_id=user.id)
            query = query.filter(Series.id.notin_(watched_ids))

    if genre:
        query = query.filter(Series.genre.ilike(f"%{genre}%"))

    series = query.order_by(sql_func.random()).first()

    if series is None:
        return jsonify({"error": "Önerilebilecek dizi bulunamadı."}), 404

    return jsonify(_serialize_series(series))


@series_bp.get("/top-rated")
def top_rated_series():
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))

    series = Series.query.filter(
        Series.rating.isnot(None)
    ).order_by(Series.rating.desc()).limit(limit).all()

    return jsonify([_serialize_series(s) for s in series])


@series_bp.get("/most-watched")
def most_watched_series():
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))

    results = db.session.query(
        Series, func.count(Watchlist.id).label("watch_count")
    ).join(Watchlist, Series.id == Watchlist.series_id).group_by(
        Series.id
    ).order_by(func.count(Watchlist.id).desc()).limit(limit).all()

    return jsonify([
        {**_serialize_series(s), "watch_count": count}
        for s, count in results
    ])


@series_bp.get("/most-reviewed")
def most_reviewed_series():
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))

    results = db.session.query(
        Series, func.count(Review.id).label("review_count")
    ).join(Review, Series.id == Review.series_id).group_by(
        Series.id
    ).order_by(func.count(Review.id).desc()).limit(limit).all()

    return jsonify([
        {**_serialize_series(s), "review_count": count}
        for s, count in results
    ])


@series_bp.get("/compare")
def compare_series():
    ids_param = request.args.get("ids", "").strip()
    if not ids_param:
        return jsonify({"error": "Karşılaştırılacak dizi id'leri gerekli (?ids=1,2)"}), 400

    try:
        series_ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
    except ValueError:
        return jsonify({"error": "Geçersiz id formatı. Örnek: ?ids=1,2"}), 400

    if len(series_ids) < 2 or len(series_ids) > 5:
        return jsonify({"error": "2 ile 5 arasında dizi seçmelisiniz."}), 400

    from app.models.favorite import Favorite

    result = []
    for sid in series_ids:
        s = Series.query.get(sid)
        if s is None:
            return jsonify({"error": f"ID {sid} ile dizi bulunamadı."}), 404

        total_reviews = Review.query.filter_by(series_id=sid).count()
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(series_id=sid).scalar()
        total_watchlist = Watchlist.query.filter_by(series_id=sid).count()
        completed = Watchlist.query.filter_by(series_id=sid, status="completed").count()
        total_favorites = Favorite.query.filter_by(series_id=sid).count()

        result.append({
            **_serialize_series(s),
            "stats": {
                "average_rating": round(float(avg_rating), 1) if avg_rating else None,
                "total_reviews": total_reviews,
                "total_watchlist": total_watchlist,
                "completed": completed,
                "total_favorites": total_favorites
            }
        })

    return jsonify(result)


@series_bp.get("/<int:series_id>")
def get_series_detail(series_id):
    s = Series.query.get_or_404(series_id)
    return jsonify(_serialize_series(s))


@series_bp.get("/<int:series_id>/stats")
def get_series_stats(series_id):
    from app.models.favorite import Favorite

    Series.query.get_or_404(series_id)

    total_reviews = Review.query.filter_by(series_id=series_id).count()
    avg_rating = db.session.query(func.avg(Review.rating)).filter_by(series_id=series_id).scalar()

    total_watchlist = Watchlist.query.filter_by(series_id=series_id).count()
    watching = Watchlist.query.filter_by(series_id=series_id, status="watching").count()
    completed = Watchlist.query.filter_by(series_id=series_id, status="completed").count()
    plan_to_watch = Watchlist.query.filter_by(series_id=series_id, status="plan_to_watch").count()
    dropped = Watchlist.query.filter_by(series_id=series_id, status="dropped").count()

    total_favorites = Favorite.query.filter_by(series_id=series_id).count()

    rating_dist = {}
    for bucket in range(1, 11):
        count = Review.query.filter(
            Review.series_id == series_id,
            Review.rating >= bucket,
            Review.rating < bucket + 1
        ).count()
        rating_dist[str(bucket)] = count

    comment_count = Review.query.filter(
        Review.series_id == series_id,
        Review.comment.isnot(None),
        Review.comment != ""
    ).count()

    return jsonify({
        "series_id": series_id,
        "average_rating": round(float(avg_rating), 1) if avg_rating else None,
        "total_reviews": total_reviews,
        "comment_count": comment_count,
        "total_favorites": total_favorites,
        "watchlist": {
            "total": total_watchlist,
            "watching": watching,
            "completed": completed,
            "plan_to_watch": plan_to_watch,
            "dropped": dropped
        },
        "rating_distribution": rating_dist
    })


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

    def _serialize_comment(r):
        return {
            "id": r.id,
            "email": r.user.email,
            "text": r.comment,
            "rating": r.rating,
            "created_at": r.created_at.isoformat()
        }

    return paginate(query, _serialize_comment)


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
