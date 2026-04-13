import pytest
import time
from app.models.user import User
from app.models.series import Series
from app.models.review import Review
from app.db import db


def log_step(test_name, input_desc, expected, actual, is_correct, start_time):
    duration = (time.time() - start_time) * 1000
    status = "[PASS]" if is_correct else "[FAIL]"
    print(f"\n--- {test_name} ---")
    print(f" > Request  : {input_desc}")
    print(f" > Expected : {expected}")
    print(f" > Actual   : {actual}")
    print(f" > Result   : {status} -- Took {duration:.2f} ms")
    print("-" * 55)


@pytest.fixture
def user_and_series(app):
    with app.app_context():
        user = User(
            email="rate@test.com",
            username="rateuser",
            password_hash=User.hash_password("pass123"),
        )
        series = Series(
            title="Peaky Blinders",
            description="İngiliz suç dizisi",
            genre="Crime",
            release_year=2013,
            rating=8.8,
            status="Ended",
        )
        db.session.add_all([user, series])
        db.session.commit()
        yield {"user_email": user.email, "series_id": series.id}


# ──────────────────────────────────────────────────────────────
# TC-REV-01: Geçerli puan verme — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_rate_series_valid(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    response = client.post(f"/api/series/{series_id}/rate", json={"rating": 8.5})
    data = response.get_json()

    is_success = response.status_code == 200 and data.get("site_rating") == 8.5

    log_step(
        "TC-REV-01 | Rate Series (Valid)",
        f"POST /api/series/{series_id}/rate {{rating: 8.5}}",
        "HTTP 200 and site_rating=8.5",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["message"] == "Puan kaydedildi."
    assert data["site_rating"] == 8.5


# ──────────────────────────────────────────────────────────────
# TC-REV-02: Geçersiz puan (sınır dışı) — 400 beklenir
# ──────────────────────────────────────────────────────────────
def test_rate_series_out_of_range(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    response = client.post(f"/api/series/{series_id}/rate", json={"rating": 11})
    data = response.get_json()

    is_success = response.status_code == 400

    log_step(
        "TC-REV-02 | Rate Series Out of Range",
        f"POST /api/series/{series_id}/rate {{rating: 11}}",
        "HTTP 400 Bad Request",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 400
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-REV-03: Rating alanı eksik — 400 beklenir
# ──────────────────────────────────────────────────────────────
def test_rate_series_missing_field(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    response = client.post(f"/api/series/{series_id}/rate", json={})
    data = response.get_json()

    is_success = response.status_code == 400

    log_step(
        "TC-REV-03 | Rate Series Missing Field",
        f"POST /api/series/{series_id}/rate {{}} (boş body)",
        "HTTP 400 Bad Request",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 400
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-REV-04: Puan güncelleme (aynı dizi için ikinci puan)
# ──────────────────────────────────────────────────────────────
def test_rate_series_update(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    with client.session_transaction() as sess:
        sess["user"] = user_and_series["user_email"]

    client.post(f"/api/series/{series_id}/rate", json={"rating": 7.0})  # ilk puan
    response = client.post(f"/api/series/{series_id}/rate", json={"rating": 9.0})  # güncelleme
    data = response.get_json()

    is_success = response.status_code == 200 and data.get("site_rating") == 9.0

    log_step(
        "TC-REV-04 | Update Existing Rating",
        f"POST /api/series/{series_id}/rate {{rating: 9.0}} (ikinci kez)",
        "HTTP 200 and site_rating=9.0 (güncellenmiş)",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["site_rating"] == 9.0


# ──────────────────────────────────────────────────────────────
# TC-REV-05: Giriş yapmadan puan verme — 401 beklenir
# ──────────────────────────────────────────────────────────────
def test_rate_series_unauthenticated(client, user_and_series):
    start = time.time()
    series_id = user_and_series["series_id"]

    # Oturum açılmadan istek
    response = client.post(f"/api/series/{series_id}/rate", json={"rating": 8.0})
    data = response.get_json()

    is_success = response.status_code == 401

    log_step(
        "TC-REV-05 | Rate Series Without Auth",
        f"POST /api/series/{series_id}/rate (oturum yok)",
        "HTTP 401 Unauthorized",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 401
    assert "error" in data
