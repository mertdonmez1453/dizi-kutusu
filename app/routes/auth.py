import re
from app.models import User
from app.db import db
from flask import Blueprint, render_template, request, redirect, session, url_for, flash

auth_bp = Blueprint("auth", __name__)

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

        if User.query.filter_by(email=email).first() is not None:
            flash("Bu e-posta adresi zaten kayıtlı.", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            email=email,
            password_hash=User.hash_password(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))
