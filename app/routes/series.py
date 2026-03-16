from flask import Blueprint, jsonify
from app.models.series import Series

series_bp = Blueprint("series", __name__, url_prefix="/api/series")

@series_bp.get("/")
def get_all_series():
    # En yüksek puanlıdan düşüğe doğru ilk 50 diziyi getirelim (sayfalandırma eklenebilir)
    series_list = Series.query.order_by(Series.rating.desc()).limit(50).all()
    
    result = []
    for s in series_list:
        result.append({
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "image_url": s.image_url,
            "rating": s.rating,
            "release_year": s.release_year,
            "genre": s.genre,
            "status": s.status,
            "trailer_url": s.trailer_url
        })
        
    return jsonify(result)

@series_bp.get("/<int:series_id>")
def get_series_detail(series_id):
    s = Series.query.get_or_404(series_id)
    return jsonify({
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "image_url": s.image_url,
        "rating": s.rating,
        "release_year": s.release_year,
        "genre": s.genre,
        "status": s.status,
        "trailer_url": s.trailer_url
    })
