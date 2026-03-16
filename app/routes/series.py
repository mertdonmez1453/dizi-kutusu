from flask import Blueprint, jsonify, request
from app.models.series import Series

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
    series_list = Series.query.order_by(Series.rating.desc()).limit(50).all()
    return jsonify([_serialize_series(s) for s in series_list])


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

    results = query.order_by(Series.rating.desc()).limit(20).all()
    return jsonify([_serialize_series(s) for s in results])


@series_bp.get("/<int:series_id>")
def get_series_detail(series_id):
    s = Series.query.get_or_404(series_id)
    return jsonify(_serialize_series(s))
