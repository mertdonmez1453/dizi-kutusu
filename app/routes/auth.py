# Login. Kullanıcı burada email ve şifre girer. 
# Eğer doğruysa maine gönderir.

from flask import Blueprint, render_template, request, redirect, url_for, session

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Eğer form gönderildiyse
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Şimdilik basit kontrol
        if email == "test@mail.com" and password == "1234":
            session["user"] = email
            return redirect(url_for("main.index"))  # giriş sonrası ana sayfa
        else:
            return "Hatalı giriş ❌"

    # Sayfa ilk açıldığında
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET"])
def register():
    return render_template("auth/register.html")