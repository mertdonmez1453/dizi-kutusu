import pytest
import time
from app.models import User
from app.db import db

from tests.logger import log_step

def test_register_page(client):
    start = time.time()
    response = client.get("/register")
    text = response.data.decode("utf-8").lower()
    
    is_success = response.status_code == 200 and ("kayıt" in text or "register" in text)
    log_step(
        "Register Page Display",
        "GET request to /register endpoint",
        "HTTP 200 OK and registration form visible",
        f"HTTP {response.status_code}, Form text found: {is_success}",
        is_success,
        start
    )
    assert response.status_code == 200
    assert "kayıt" in text or "register" in text

def test_login_page(client):
    start = time.time()
    response = client.get("/login")
    text = response.data.decode("utf-8").lower()
    
    is_success = response.status_code == 200 and ("giriş" in text or "login" in text)
    log_step(
        "Login Page Display",
        "GET request to /login endpoint",
        "HTTP 200 OK and login form visible",
        f"HTTP {response.status_code}, Form text found: {is_success}",
        is_success,
        start
    )
    assert response.status_code == 200
    assert "giriş" in text or "login" in text

def test_register_success(client, app):
    start = time.time()
    response = client.post("/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        user_exists = user is not None
        password_valid = user.check_password("password123") if user else False
        
    is_success = response.status_code == 200 and user_exists and password_valid
    
    log_step(
        "Valid Registration",
        "POST to /register with valid email & password",
        "Account created in database and hashed password matches",
        f"HTTP {response.status_code}, User saved to DB: {user_exists}, Password match: {password_valid}",
        is_success,
        start
    )
    
    assert response.status_code == 200
    assert user_exists
    assert password_valid

def test_register_invalid_email(client, app):
    start = time.time()
    response = client.post("/register", data={
        "username": "invaliduser",
        "email": "invalid-email",
        "password": "password123"
    }, follow_redirects=True)
    
    with app.app_context():
        user = User.query.filter_by(email="invalid-email").first()
        user_not_created = user is None
        
    is_success = user_not_created
    
    log_step(
        "Invalid Email Registration",
        "POST to /register with badly formatted email",
        "Registration rejected; no user added to database",
        f"Database user creation blocked: {user_not_created}",
        is_success,
        start
    )
    
    assert user_not_created

def test_register_existing_email(client, app):
    with app.app_context():
        user = User(email="test2@example.com", username="testuser2", password_hash=User.hash_password("password123"))
        db.session.add(user)
        db.session.commit()

    start = time.time()
    response = client.post("/register", data={
        "username": "dupeuser",
        "email": "test2@example.com",
        "password": "newpassword456"
    }, follow_redirects=True)
    
    with app.app_context():
        users = User.query.filter_by(email="test2@example.com").all()
        count_is_one = len(users) == 1
        password_did_not_change = users[0].check_password("password123") if count_is_one else False

    is_success = count_is_one and password_did_not_change
    
    log_step(
        "Duplicate Registration",
        "POST to /register with an already existing email",
        "Registration rejected; no duplicate user and original password preserved",
        f"Duplicate prevented: {count_is_one}, Password preserved: {password_did_not_change}",
        is_success,
        start
    )
    
    assert count_is_one
    assert password_did_not_change

def test_login_success(client, app):
    with app.app_context():
        user = User(email="login@example.com", username="loginuser", password_hash=User.hash_password("password123"))
        db.session.add(user)
        db.session.commit()

    start = time.time()
    response = client.post("/login", data={
        "email": "login@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        session_user = sess.get("user")
        
    is_success = response.status_code == 200 and session_user == "login@example.com"
    
    log_step(
        "Valid Login",
        "POST to /login with correct registered email & password",
        "HTTP 200 OK and user email saved inside Session",
        f"HTTP {response.status_code}, Session user active: {session_user}",
        is_success,
        start
    )
    
    assert response.status_code == 200
    assert session_user == "login@example.com"

def test_login_invalid_password(client, app):
    with app.app_context():
        user = User(email="login2@example.com", username="loginuser2", password_hash=User.hash_password("password123"))
        db.session.add(user)
        db.session.commit()

    start = time.time()
    response = client.post("/login", data={
        "email": "login2@example.com",
        "password": "wrongpassword"
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        session_user = sess.get("user")
        
    is_success = session_user is None
    
    log_step(
        "Invalid Login Password",
        "POST to /login with correct email but wrong password",
        "Login blocked; Session remains empty",
        f"Session user active: {session_user} (Expected None)",
        is_success,
        start
    )
    
    assert session_user is None

def test_login_nonexistent_user(client):
    start = time.time()
    response = client.post("/login", data={
        "email": "nobody@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        session_user = sess.get("user")
        
    is_success = session_user is None
    
    log_step(
        "Unknown User Login",
        "POST to /login with unregistered email address",
        "Login blocked; Session remains empty",
        f"Session user active: {session_user} (Expected None)",
        is_success,
        start
    )
    
    assert session_user is None

def test_logout(client, app):
    start = time.time()
    with client.session_transaction() as sess:
        sess["user"] = "logout_test@example.com"
        
    response = client.get("/logout", follow_redirects=True)
    
    with client.session_transaction() as sess:
        session_user = sess.get("user")
        
    is_success = session_user is None
    
    log_step(
        "User Logout",
        "GET request to /logout with active logged-in Session",
        "Session cleared of user data successfully",
        f"Session user active: {session_user} (Expected None)",
        is_success,
        start
    )
    
    assert session_user is None
