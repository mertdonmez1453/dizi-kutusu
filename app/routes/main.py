# Ana sayfa. Giriş yaptıktan sonra buraya gelir.

from flask import Blueprint, render_template, redirect, url_for, flash, g
from app.utils import login_required


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def root():
    return redirect(url_for("auth.login"))


@main_bp.get("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")


@main_bp.get("/reset-password")
def reset_password():
    return render_template("auth/reset_password.html")


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


@main_bp.get("/friends")
@login_required
def friends():
    return render_template("friends.html")


@main_bp.get("/friends/<int:user_id>")
@login_required
def friend_profile(user_id):
    return render_template("friend_profile.html", user_id=user_id)


@main_bp.get("/compare")
@login_required
def compare():
    return render_template("compare.html")


@main_bp.get("/admin")
@login_required
def admin():
    if not g.current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz yok.", "error")
        return redirect(url_for("main.index"))
    return render_template("admin.html")
