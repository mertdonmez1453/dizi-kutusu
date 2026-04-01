# Ana sayfa. Giriş yaptıktan sonra buraya gelir.

from flask import Blueprint, render_template, redirect, url_for
from app.utils import login_required


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def root():
    return redirect(url_for("auth.login"))


@main_bp.get("/main")
@login_required
def index():
    return render_template("auth/main.html")


@main_bp.get("/series/<int:series_id>")
@login_required
def series_detail(series_id):
    return render_template("series_detail.html", series_id=series_id)


@main_bp.get("/profile")
@login_required
def profile():
    return render_template("profile.html")


@main_bp.get("/settings")
@login_required
def settings():
    return render_template("settings.html")
