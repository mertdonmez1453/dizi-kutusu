import pytest
import time
from app.models.user import User
from app.models.series import Series
from app.models.favorite import Favorite
from app.db import db


from tests.logger import log_step


@pytest.fixture
def user_and_series(app):
    with app.app_context():
        user = User(
            email="fav@test.com",
            username="favuser",
            password_hash=User.hash_password("pass123"),
        )
        series = Series(
            title="Squid Game",
            description="Kore hayatta kalma dizisi",
            genre="Thriller",
            release_year=2021,
            rating=8.0,
            status="Ongoing",
        )
        db.session.add_all([user, series])
        db.session.commit()
        yield {"user_email": user.email, "series_id": series.id}


# ──────────────────────────────────────────────────────────────
# TC-FAV-01: Favorilere dizi ekleme — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_add_favorite(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    response = client.post(f"/api/favorites/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 201 and "message" in data

    log_step(
        "TC-FAV-01 | Add to Favorites",
        f"POST /api/favorites/{series_id} (oturum açık)",
        "HTTP 201 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 201
    assert data["message"] == "Favorilere eklendi."


# ──────────────────────────────────────────────────────────────
# TC-FAV-02: Aynı diziyi tekrar favorilere ekleme — 409 beklenir
# ──────────────────────────────────────────────────────────────
def test_add_favorite_duplicate(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/favorites/{series_id}")  # ilk ekleme
    response = client.post(f"/api/favorites/{series_id}")  # tekrar ekleme
    data = response.get_json()

    is_success = response.status_code == 409

    log_step(
        "TC-FAV-02 | Duplicate Favorite Add",
        f"POST /api/favorites/{series_id} (zaten favorilerde)",
        "HTTP 409 Conflict",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 409
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-FAV-03: Favorilerden dizi kaldırma — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_remove_favorite(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/favorites/{series_id}")  # önce ekle
    response = client.delete(f"/api/favorites/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 200 and "message" in data

    log_step(
        "TC-FAV-03 | Remove from Favorites",
        f"DELETE /api/favorites/{series_id}",
        "HTTP 200 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["message"] == "Favorilerden kaldırıldı."


# ──────────────────────────────────────────────────────────────
# TC-FAV-04: Giriş yapmadan favori ekleme — 401 beklenir
# ──────────────────────────────────────────────────────────────
def test_add_favorite_unauthenticated(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    # Oturum açılmadan istek
    response = client.post(f"/api/favorites/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 401

    log_step(
        "TC-FAV-04 | Add Favorite Without Auth",
        f"POST /api/favorites/{series_id} (oturum yok)",
        "HTTP 401 Unauthorized",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 401
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-FAV-05: Favorilerde olmayan diziyi silme — 404 beklenir
# ──────────────────────────────────────────────────────────────
def test_remove_nonexistent_favorite(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    # Eklenmeden silmeye çalış
    response = client.delete(f"/api/favorites/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 404

    log_step(
        "TC-FAV-05 | Remove Non-Existent Favorite",
        f"DELETE /api/favorites/{series_id} (favorilerde yok)",
        "HTTP 404 Not Found",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 404
    assert "error" in data
