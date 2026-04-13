import pytest
import time
from app.models.series import Series
from app.db import db


from tests.logger import log_step


def make_series(**kwargs):
    """Varsayılan zorunlu alanlarla birlikte Series objesi oluşturur."""
    defaults = {
        "title": "Test Dizisi",
        "description": "Test açıklaması",
        "genre": "Drama",
        "release_year": 2020,
        "rating": 7.5,
        "status": "Ended",
    }
    defaults.update(kwargs)
    return Series(**defaults)


# ──────────────────────────────────────────────────────────────
# TC-SER-01: Başlık ile dizi arama — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_search_series_by_title(client, app):
    start = time.time()
    with app.app_context():
        s = make_series(title="Breaking Bad", genre="Crime", release_year=2008, rating=9.5)
        db.session.add(s)
        db.session.commit()

    response = client.get("/api/series/search?q=Breaking")
    data = response.get_json()

    # paginate() sayfa parametresi olmadan düz liste döner
    titles = [item["title"] for item in data]
    is_success = response.status_code == 200 and any(t == "Breaking Bad" for t in titles)

    log_step(
        "TC-SER-01 | Series Search by Title",
        "GET /api/series/search?q=Breaking",
        "HTTP 200 and 'Breaking Bad' in results",
        f"HTTP {response.status_code}, Titles: {titles}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert any(item["title"] == "Breaking Bad" for item in data)


# ──────────────────────────────────────────────────────────────
# TC-SER-02: Hiç parametre gönderilmeden arama — 400 beklenir
# ──────────────────────────────────────────────────────────────
def test_search_series_no_params(client):
    start = time.time()
    response = client.get("/api/series/search")
    data = response.get_json()

    is_success = response.status_code == 400 and "error" in data

    log_step(
        "TC-SER-02 | Series Search Without Params",
        "GET /api/series/search (parametre yok)",
        "HTTP 400 and error message in response",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 400
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-SER-03: Genre ile filtreleme
# ──────────────────────────────────────────────────────────────
def test_search_series_by_genre(client, app):
    start = time.time()
    with app.app_context():
        s1 = make_series(title="Sci-Fi Show", genre="Sci-Fi")
        s2 = make_series(title="Comedy Show", genre="Comedy")
        db.session.add_all([s1, s2])
        db.session.commit()

    response = client.get("/api/series/search?genre=Sci-Fi")
    data = response.get_json()

    genres_returned = [item["genre"] for item in data]
    is_success = response.status_code == 200 and all("Sci-Fi" in g for g in genres_returned)

    log_step(
        "TC-SER-03 | Series Search by Genre",
        "GET /api/series/search?genre=Sci-Fi",
        "HTTP 200, only Sci-Fi results",
        f"HTTP {response.status_code}, Genres: {genres_returned}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert all("Sci-Fi" in item["genre"] for item in data)
