# Ana sayfa. Giriş yaptıktan sonra buraya gelir.

from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)

# Ana link her zaman login'e gitsin
@main_bp.get("/")
def root():
    return redirect(url_for("auth.login"))

# Main sayfa ayrı bir endpoint olsun
@main_bp.get("/main")
def index():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("auth/main.html")