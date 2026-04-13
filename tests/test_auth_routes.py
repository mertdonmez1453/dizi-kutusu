import pytest
from app.models.user import User
from app.db import db


@pytest.fixture
def init_database(app):
    """test@test.com / password123 kullanıcısını DB'ye ekler."""
    with app.app_context():
        user = User(
            email="test@test.com",
            username="testuser",
            password_hash=User.hash_password("password123"),
        )
        db.session.add(user)
        db.session.commit()
    yield


# ── Register ────────────────────────────────────────────────

def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"form" in response.data.lower()


def test_user_registration(client, app):
    response = client.post("/register", data={
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "newpassword123"
    })

    # Başarılı kayıt → /login'e 302 redirect
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Kullanıcı DB'ye eklendi mi?
    with app.app_context():
        user = User.query.filter_by(email="newuser@test.com").first()
        assert user is not None
        assert user.check_password("newpassword123")


def test_user_registration_existing_email(client, init_database):
    # init_database: test@test.com zaten kayıtlı
    response = client.post("/register", data={
        "username": "anotheruser",
        "email": "test@test.com",
        "password": "anotherpassword"
    })

    # Hata durumunda /register'a geri redirect (302)
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]


def test_user_registration_missing_username(client):
    # username olmadan kayıt → hata redirect
    response = client.post("/register", data={
        "email": "nousername@test.com",
        "password": "password123"
    })
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]


def test_user_registration_invalid_email(client):
    # Geçersiz email → /register'a redirect
    response = client.post("/register", data={
        "username": "validuser",
        "email": "not-an-email",
        "password": "password123"
    })
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]


# ── Login ────────────────────────────────────────────────────

def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"form" in response.data.lower()


def test_user_login(client, init_database):
    response = client.post("/login", data={
        "email": "test@test.com",
        "password": "password123"
    })

    # Başarılı giriş → /main'e 302 redirect
    assert response.status_code == 302
    assert "/main" in response.headers["Location"]

    # Session'da kullanıcı emaili var mı?
    with client.session_transaction() as sess:
        assert sess.get("user") == "test@test.com"


def test_user_login_incorrect_password(client, init_database):
    response = client.post("/login", data={
        "email": "test@test.com",
        "password": "wrongpassword"
    })

    # Yanlış şifre → /login'e redirect
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Session boş olmalı
    with client.session_transaction() as sess:
        assert sess.get("user") is None


def test_user_login_nonexistent_user(client):
    response = client.post("/login", data={
        "email": "notfound@test.com",
        "password": "password123"
    })

    # Olmayan kullanıcı → /login'e redirect
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ── Logout ───────────────────────────────────────────────────

def test_logout(client):
    with client.session_transaction() as sess:
        sess["user"] = "test@test.com"

    response = client.get("/logout")

    # Logout → /login'e redirect
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Session temizlendi mi?
    with client.session_transaction() as sess:
        assert sess.get("user") is None
