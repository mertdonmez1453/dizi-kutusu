# Ana sayfa. Giriş yaptıktan sonra buraya gelir.

from flask import Blueprint, render_template, redirect, url_for, jsonify
from app.models.user import User
from app.utils import login_required


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def root():
    return redirect(url_for("auth.login"))


@main_bp.get("/main")
@login_required
def index():
    return render_template("auth/main.html")


@main_bp.get("/users")
@login_required
def list_users():
    users = User.query.all()

    result = []
    for u in users:
        result.append({
            "id": u.id,
            "email": u.email,
            "created_at": u.created_at
        })

    return jsonify(result)
