import pytest
import time
from app.models.user import User
from app.models.series import Series
from app.models.watchlist import Watchlist
from app.db import db


from tests.logger import log_step


@pytest.fixture
def user_and_series(app):
    """Giriş yapmış kullanıcı + dizi fixture'ı döner."""
    with app.app_context():
        user = User(
            email="wl@test.com",
            username="wluser",
            password_hash=User.hash_password("pass123"),
        )
        series = Series(
            title="Dark",
            description="Alman bilim kurgu dizisi",
            genre="Sci-Fi",
            release_year=2017,
            rating=8.8,
            status="Ended",
        )
        db.session.add_all([user, series])
        db.session.commit()
        yield {"user_email": user.email, "series_id": series.id}


# ──────────────────────────────────────────────────────────────
# TC-WL-01: İzleme listesine dizi ekleme — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_add_to_watchlist(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    response = client.post(f"/api/watchlist/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 201 and "message" in data

    log_step(
        "TC-WL-01 | Add to Watchlist",
        f"POST /api/watchlist/{series_id} (oturum açık)",
        "HTTP 201 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 201
    assert data["message"] == "İzleme listesine eklendi."


# ──────────────────────────────────────────────────────────────
# TC-WL-02: Aynı diziyi tekrar ekleme — 409 beklenir
# ──────────────────────────────────────────────────────────────
def test_add_to_watchlist_duplicate(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/watchlist/{series_id}")  # ilk ekleme
    response = client.post(f"/api/watchlist/{series_id}")  # tekrar ekleme
    data = response.get_json()

    is_success = response.status_code == 409

    log_step(
        "TC-WL-02 | Duplicate Watchlist Add",
        f"POST /api/watchlist/{series_id} (zaten listede)",
        "HTTP 409 Conflict",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 409
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-WL-03: Giriş yapmadan izleme listesine erişim — 401 beklenir
# ──────────────────────────────────────────────────────────────
def test_watchlist_unauthenticated(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    response = client.post(f"/api/watchlist/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 401

    log_step(
        "TC-WL-03 | Watchlist Without Auth",
        f"POST /api/watchlist/{series_id} (oturum yok)",
        "HTTP 401 Unauthorized",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 401
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-WL-04: İzleme listesinden dizi silme — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_remove_from_watchlist(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/watchlist/{series_id}")  # önce ekle
    response = client.delete(f"/api/watchlist/{series_id}")
    data = response.get_json()

    is_success = response.status_code == 200 and "message" in data

    log_step(
        "TC-WL-04 | Remove from Watchlist",
        f"DELETE /api/watchlist/{series_id}",
        "HTTP 200 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["message"] == "İzleme listesinden kaldırıldı."


# ──────────────────────────────────────────────────────────────
# TC-WL-05: Watchlist status güncelleme — geçerli durum
# ──────────────────────────────────────────────────────────────
def test_update_watchlist_status(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/watchlist/{series_id}")  # önce ekle (plan_to_watch)
    response = client.put(f"/api/watchlist/{series_id}/status", json={"status": "watching"})
    data = response.get_json()

    is_success = response.status_code == 200 and data.get("status") == "watching"

    log_step(
        "TC-WL-05 | Update Watchlist Status",
        f"PUT /api/watchlist/{series_id}/status {{status: watching}}",
        "HTTP 200 and status='watching'",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["status"] == "watching"
