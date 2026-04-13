import pytest
import time
from app.models.user import User
from app.models.friendship import Friendship
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
def two_users(app):
    """İki kullanıcı oluşturur; user_a takip eden, user_b takip edilen."""
    with app.app_context():
        user_a = User(
            email="a@test.com",
            username="usera",
            password_hash=User.hash_password("pass123"),
        )
        user_b = User(
            email="b@test.com",
            username="userb",
            password_hash=User.hash_password("pass123"),
        )
        db.session.add_all([user_a, user_b])
        db.session.commit()
        yield {
            "a_email": user_a.email,
            "a_id": user_a.id,
            "b_id": user_b.id,
            "b_username": user_b.username,
        }


# ──────────────────────────────────────────────────────────────
# TC-FR-01: Başarılı takip etme
# ──────────────────────────────────────────────────────────────
def test_follow_user(client, two_users):
    start = time.time()
    b_id = two_users["b_id"]

    with client.session_transaction() as sess:
        sess["user"] = two_users["a_email"]

    response = client.post(f"/api/friendships/follow/{b_id}")
    data = response.get_json()

    is_success = response.status_code == 201 and "message" in data

    log_step(
        "TC-FR-01 | Follow User",
        f"POST /api/friendships/follow/{b_id}",
        "HTTP 201 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 201
    assert "takip edildi" in data["message"]


# ──────────────────────────────────────────────────────────────
# TC-FR-02: Aynı kullanıcıyı tekrar takip etme — 409 beklenir
# ──────────────────────────────────────────────────────────────
def test_follow_user_duplicate(client, two_users):
    start = time.time()
    b_id = two_users["b_id"]

    with client.session_transaction() as sess:
        sess["user"] = two_users["a_email"]

    client.post(f"/api/friendships/follow/{b_id}")  # ilk takip
    response = client.post(f"/api/friendships/follow/{b_id}")  # tekrar
    data = response.get_json()

    is_success = response.status_code == 409

    log_step(
        "TC-FR-02 | Duplicate Follow",
        f"POST /api/friendships/follow/{b_id} (zaten takipte)",
        "HTTP 409 Conflict",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 409
    assert "error" in data


# ──────────────────────────────────────────────────────────────
# TC-FR-03: Kendini takip etme — 400 beklenir
# ──────────────────────────────────────────────────────────────
def test_cannot_follow_self(client, two_users):
    start = time.time()
    a_id = two_users["a_id"]

    with client.session_transaction() as sess:
        sess["user"] = two_users["a_email"]

    response = client.post(f"/api/friendships/follow/{a_id}")
    data = response.get_json()

    is_success = response.status_code == 400 and "Kendinizi takip edemezsiniz" in data.get("error", "")

    log_step(
        "TC-FR-03 | Follow Self",
        f"POST /api/friendships/follow/{a_id} (kendi id'si)",
        "HTTP 400 and 'Kendinizi takip edemezsiniz.' error",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 400
    assert "Kendinizi takip edemezsiniz" in data["error"]


# ──────────────────────────────────────────────────────────────
# TC-FR-04: Takipten çıkma — başarılı senaryo
# ──────────────────────────────────────────────────────────────
def test_unfollow_user(client, two_users):
    start = time.time()
    b_id = two_users["b_id"]

    with client.session_transaction() as sess:
        sess["user"] = two_users["a_email"]

    client.post(f"/api/friendships/follow/{b_id}")  # önce takip et
    response = client.delete(f"/api/friendships/unfollow/{b_id}")
    data = response.get_json()

    is_success = response.status_code == 200 and "message" in data

    log_step(
        "TC-FR-04 | Unfollow User",
        f"DELETE /api/friendships/unfollow/{b_id}",
        "HTTP 200 and success message",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 200
    assert data["message"] == "Takipten çıkıldı."


# ──────────────────────────────────────────────────────────────
# TC-FR-05: Takip edilmeyen birinin listesini görme — 403 beklenir
# ──────────────────────────────────────────────────────────────
def test_view_friend_watchlist_without_following(client, two_users):
    start = time.time()
    b_id = two_users["b_id"]

    with client.session_transaction() as sess:
        sess["user"] = two_users["a_email"]

    # Takip etmeden b'nin watchlist'ini görmeye çalış
    response = client.get(f"/api/friendships/{b_id}/watchlist")
    data = response.get_json()

    is_success = response.status_code == 403

    log_step(
        "TC-FR-05 | View Watchlist Without Following",
        f"GET /api/friendships/{b_id}/watchlist (takip yok)",
        "HTTP 403 Forbidden",
        f"HTTP {response.status_code}, Body: {data}",
        is_success,
        start,
    )

    assert response.status_code == 403
    assert "error" in data
