# EPISODE ROUTES: Dizi bölümleriyle ilgili tüm API endpoint'leri.

from flask import Blueprint, jsonify, request
from app.db import db
from app.models.series import Series
from app.models.episode import Episode

episode_bp = Blueprint("episode", __name__, url_prefix="/api/episodes")


# QUERY: Belirli bir dizinin tüm bölümlerini sezon ve bölüm sırasına göre getirir (SELECT + ORDER BY)
@episode_bp.get("/series/<int:series_id>")
def get_episodes_for_series(series_id):
    # QUERY: Dizinin var olup olmadığını kontrol eder (SELECT)
    series = Series.query.get_or_404(series_id)

    episodes = Episode.query.filter_by(series_id=series_id)\
        .order_by(Episode.season_number, Episode.episode_number).all()

    result = []
    for ep in episodes:
        result.append({
            "id": ep.id,
            "season_number": ep.season_number,
            "episode_number": ep.episode_number,
            "title": ep.title,
            "air_date": ep.air_date.isoformat() if ep.air_date else None
        })
    return jsonify({
        "series_title": series.title,
        "episodes": result
    })


# QUERY: Bir diziye yeni bölüm ekler (INSERT)
@episode_bp.post("/add")
def add_episode():
    data = request.get_json()
    series_id = data.get("series_id")
    season_number = data.get("season_number")
    episode_number = data.get("episode_number")
    title = data.get("title", "")

    # QUERY: Dizinin veritabanında var olup olmadığını kontrol eder (SELECT)
    series = Series.query.get(series_id)
    if not series:
        return jsonify({"error": "Dizi bulunamadı"}), 404

    # QUERY: Aynı sezon-bölüm kombinasyonunun daha önce eklenip eklenmediğini kontrol eder (SELECT)
    existing = Episode.query.filter_by(
        series_id=series_id,
        season_number=season_number,
        episode_number=episode_number
    ).first()
    if existing:
        return jsonify({"error": "Bu bölüm zaten mevcut"}), 409

    new_ep = Episode(
        series_id=series_id,
        season_number=season_number,
        episode_number=episode_number,
        title=title
    )
    db.session.add(new_ep)
    db.session.commit()

    return jsonify({"message": f"S{season_number:02d}E{episode_number:02d} eklendi"}), 201
