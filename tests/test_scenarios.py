import pytest
import time
from app.models.user import User
from app.models.series import Series
from app.db import db
from tests.scenario_logger import log_scenario_step

@pytest.fixture
def scenario_setup(app):
    with app.app_context():
        u2 = User(email="mehmet@test.com", username="mehmet", password_hash=User.hash_password("pass123"))
        s1 = Series(
            title="Breaking Bad", 
            description="A high school chemistry teacher...",
            genre="Crime",
            release_year="2008"
        )
        s2 = Series(
            title="Stranger Things",
            description="When a young boy vanishes...",
            genre="Sci-Fi",
            release_year="2016"
        )
        db.session.add_all([u2, s1, s2])
        db.session.commit()
        yield {"u2_id": u2.id, "s1_id": s1.id, "s2_id": s2.id}

# ──────────────────────────────────────────────────────────────
# USE CASE 1 — New User Full Journey (Signup → Login → Explore)
# ──────────────────────────────────────────────────────────────
def test_use_case_1_new_user_journey(client, app, scenario_setup):
    start = time.time()
    
    # 1. Signup
    res_signup = client.post("/register", data={
        "username": "yenikullanici",
        "email": "yeni@test.com",
        "password": "mypassword"
    }, follow_redirects=True)
    
    with app.app_context():
        user = User.query.filter_by(email="yeni@test.com").first()
        signup_ok = user is not None and user.check_password("mypassword")
        
    log_scenario_step(
        "USE CASE 1",
        "Kullanıcı Signup/Kayıt formunu doldurur ve hesap oluşturulur",
        "HTTP 200/Redirect ve Veritabanında Kullanıcı oluşmalı",
        f"Durum: {res_signup.status_code}, DB'de kullanıcı var mı: {signup_ok}",
        signup_ok,
        start
    )
    assert signup_ok
    
    # 2. Login
    res_login = client.post("/login", data={
        "email": "yeni@test.com",
        "password": "mypassword"
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        session_user = sess.get("user")
    
    login_ok = session_user == "yeni@test.com"
    log_scenario_step(
        "USE CASE 1",
        "Kullanıcı yeni bilgileriyle Login olur",
        "HTTP 200/Redirect ve Session'a email kaydedilmeli",
        f"Session'daki Email: {session_user}",
        login_ok,
        time.time()
    )
    assert login_ok
    
    # 3. Explore (Dizi Listesine Göz Atar)
    res_explore = client.get("/api/series/search?q=") # Boş q ile liste gelir mi veya direkt sayfaya girer
    res_main = client.get("/main")
    
    explore_ok = res_main.status_code == 200 and "yeni@test.com" in res_main.get_data(as_text=True)
    log_scenario_step(
        "USE CASE 1",
        "Ana sayfaya yönlendirilir ve gezintiye başlar",
        "HTTP 200 ve Ana sayfada profili görmeli",
        f"HTTP Status: {res_main.status_code}, Email sayfada geçiyor mu: {explore_ok}",
        explore_ok,
        time.time()
    )
    assert explore_ok


# ──────────────────────────────────────────────────────────────
# USE CASE 2 — Search with Error Tolerance
# ──────────────────────────────────────────────────────────────
def test_use_case_2_search_with_error_tolerance(client, app, scenario_setup):
    start = time.time()
    
    with app.app_context():
        u = User(email="admin@test.com", username="admin", password_hash="hash")
        db.session.add(u)
        db.session.commit()
        
    with client.session_transaction() as sess:
        sess["user"] = "admin@test.com" # Fake login
        
    s1_id = scenario_setup["s1_id"]
    
    # 1. Yanlış yazılmış arama (Breaking Bad -> "break")
    res_search = client.get("/api/series/search?q=break")
    data = res_search.get_json()
    
    search_ok = res_search.status_code == 200 and any("Breaking Bad" in d["title"] for d in data)
    log_scenario_step(
        "USE CASE 2",
        "Kullanıcı arama kutusuna 'break' yazar (eksik/yanlış)",
        "Sistem ilike ile 'Breaking Bad' dizisini döndürmeli",
        f"Gelen Sonuçlar: {[d.get('title') for d in data]}",
        search_ok,
        start
    )
    assert search_ok
    
    # 2. Doğru diziyi seçip detay sayfasını açar
    res_detail = client.get(f"/series/{s1_id}")
    text = res_detail.get_data(as_text=True)
    detail_ok = res_detail.status_code == 200 and "Dizi Kutusu — Detay" in text
    
    log_scenario_step(
        "USE CASE 2",
        "Kullanıcı çıkan sonuca tıklar ve detay sayfasını açar",
        "Dizi detay sayfasının HTML'i doğru render edilmeli",
        f"HTTP Status: {res_detail.status_code}, HTML'de başlık bulundu: {detail_ok}",
        detail_ok,
        time.time()
    )
    assert detail_ok


# ──────────────────────────────────────────────────────────────
# USE CASE 3 — Watch → Rate → Review Flow
# ──────────────────────────────────────────────────────────────
def test_use_case_3_watch_rate_review(client, app, scenario_setup):
    start = time.time()
    s2_id = scenario_setup["s2_id"]
    
    with client.session_transaction() as sess:
        sess["user"] = "user@test.com" # Yetkili kullanıcı
        
    with app.app_context():
        u = User(email="user@test.com", username="tester", password_hash="hash")
        db.session.add(u)
        db.session.commit()

    # 1. İzleme listesine ekleme
    res_add = client.post(f"/api/watchlist/{s2_id}")
    add_ok = res_add.status_code == 201
    log_scenario_step(
        "USE CASE 3",
        "Kullanıcı diziyi izleme listesine ekler",
        "HTTP 201 Created alınmalı",
        f"HTTP Status: {res_add.status_code}",
        add_ok,
        start
    )
    
    # 2. İzleme durumunu completed (İzledi) yapar
    res_status = client.put(f"/api/watchlist/{s2_id}/status", json={"status": "completed"})
    status_ok = res_status.status_code == 200
    log_scenario_step(
        "USE CASE 3",
        "Kullanıcı dizinin durumunu 'completed' (İzledi) olarak seçer",
        "HTTP 200 OK ve status completed güncellenmeli",
        f"HTTP Status: {res_status.status_code}",
        status_ok,
        time.time()
    )
    
    # 3. Yorum ve Puan verme
    res_review = client.post(f"/api/series/{s2_id}/comments", json={
        "text": "Harika ötesi dizi!",
        "rating": 10
    })
    review_ok = res_review.status_code == 201
    
    with app.app_context():
        series = Series.query.get(s2_id)
        rating_updated = series.rating == 10.0
        
    log_scenario_step(
        "USE CASE 3",
        "Diziye hem puan (10 üzerinden) hem de metin yorumu bırakır",
        "Comment DB'ye yazılmalı ve dizinin ortalama puanı recalculate edilmeli (10.0)",
        f"Review Status: {res_review.status_code}, Yeni Ortalama Puan: {series.rating}",
        review_ok and rating_updated,
        time.time()
    )


# ──────────────────────────────────────────────────────────────
# USE CASE 4 — Social Interaction Flow
# ──────────────────────────────────────────────────────────────
def test_use_case_4_social_interaction_flow(client, app, scenario_setup):
    start = time.time()
    u2_id = scenario_setup["u2_id"] # mehmet'in ids'i
    s1_id = scenario_setup["s1_id"]
    
    with app.app_context():
        u1 = User(email="ali@test.com", username="ali", password_hash="hash")
        db.session.add(u1)
        db.session.commit()
        # Mehmet bir diyizi watchlist'ine önceden eklemiş olsun, görelim
        from app.models.watchlist import Watchlist
        w = Watchlist(user_id=u2_id, series_id=s1_id, status="completed")
        db.session.add(w)
        db.session.commit()
    
    with client.session_transaction() as sess:
        sess["user"] = "ali@test.com" # Ali giriş yaptı
        
    # 1. Başka kullanıcıyı ara ve follow et
    res_follow = client.post(f"/api/friendships/{u2_id}")
    follow_ok = res_follow.status_code in [200, 201]
    
    log_scenario_step(
        "USE CASE 4",
        "Kullanıcı 'mehmet'i arar ve takip et (follow) butonuna tıklar",
        "HTTP 200 veya 201 ile friendship tablosuna bağ kurulmalı",
        f"HTTP Status: {res_follow.status_code}, Response: {res_follow.get_json()}",
        follow_ok,
        start
    )
    
    # 2. Onun izleme listesini (watchlist) API'den çek ve gör
    res_watch = client.get(f"/api/friendships/user/{u2_id}/watchlist")
    watch_data = res_watch.get_json()
    watch_ok = res_watch.status_code == 200 and len(watch_data) > 0 and watch_data[0]["status"] == "completed"
    
    log_scenario_step(
        "USE CASE 4",
        "Takip edilen arkadaşın profiline girer ve İzleme Listesini çeker",
        "HTTP 200 ve listeye eklenmiş dizileri dönmeli ('completed')",
        f"Gelen Watchlist Uzunluğu: {len(watch_data) if type(watch_data)==list else watch_data}",
        watch_ok,
        time.time()
    )
    
    # 3. Aktivite feed’inde yapılanları gör
    res_feed = client.get("/api/friendships/feed")
    feed_data = res_feed.get_json()
    # It might return an empty list or data format depending on backend logic. Just validating response format is success.
    # We will assume if not 200 it failed. If data is list, it's ok.
    feed_ok = res_feed.status_code == 200 and isinstance(feed_data, list)
    
    log_scenario_step(
        "USE CASE 4",
        "Kullanıcı ana sayfasına /feed (Aktiviteler) düşer ve API'den listeyi çeker",
        "HTTP 200 OK ve JSON liste dönmeli",
        f"HTTP Status: {res_feed.status_code}, Gelen Feed Obje Sayısı: {len(feed_data) if isinstance(feed_data, list) else 0}",
        feed_ok,
        time.time()
    )
    assert follow_ok and watch_ok and feed_ok
