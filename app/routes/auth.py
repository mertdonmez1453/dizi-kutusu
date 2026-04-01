import re
from app.models import User
from app.db import db
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

auth_bp = Blueprint("auth", __name__)


def _get_reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("E-posta ve şifre alanları boş bırakılamaz.", "error")
            return redirect(url_for("auth.login"))

        # QUERY: Verilen email adresine sahip kullanıcıyı veritabanında arar (Login Query)
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("E-posta veya şifre hatalı.", "error")
            return redirect(url_for("auth.login"))

        session["user"] = user.email
        return redirect(url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Tüm alanlar doldurulmalıdır.", "error")
            return redirect(url_for("auth.register"))

        if not EMAIL_REGEX.match(email):
            flash("Geçerli bir e-posta adresi giriniz.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Şifre en az 6 karakter olmalıdır.", "error")
            return redirect(url_for("auth.register"))

        # QUERY: Kayıt olmak istenen email adresinin daha önce alınıp alınmadığını kontrol eder (Search Query)
        if User.query.filter_by(email=email).first() is not None:
            flash("Bu e-posta adresi zaten kayıtlı.", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            email=email,
            password_hash=User.hash_password(password)
        )
        # QUERY: Yeni kullanıcıyı veritabanına ekler ve kaydeder (Insert Query)
        db.session.add(new_user)
        db.session.commit()

        flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))


@auth_bp.post("/api/auth/forgot-password")
def forgot_password():
    data = request.get_json(silent=True)
    if not data or not data.get("email", "").strip():
        return jsonify({"error": "E-posta adresi gerekli."}), 400

    email = data["email"].strip()
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı."}), 404

    s = _get_reset_serializer()
    token = s.dumps(email, salt="password-reset")

    return jsonify({
        "message": "Sıfırlama token'ı oluşturuldu.",
        "token": token
    })


@auth_bp.post("/api/auth/reset-password")
def reset_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")

    if not token or not new_password:
        return jsonify({"error": "Token ve yeni şifre alanları zorunludur."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Yeni şifre en az 6 karakter olmalıdır."}), 400

    s = _get_reset_serializer()
    try:
        email = s.loads(token, salt="password-reset", max_age=1800)
    except SignatureExpired:
        return jsonify({"error": "Token süresi dolmuş. Lütfen tekrar deneyin."}), 400
    except BadSignature:
        return jsonify({"error": "Geçersiz token."}), 400

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"error": "Kullanıcı bulunamadı."}), 404

    user.password_hash = User.hash_password(new_password)
    db.session.commit()

    return jsonify({"message": "Şifre başarıyla güncellendi."})
