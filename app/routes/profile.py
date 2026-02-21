from flask import Blueprint, request, jsonify, g
from app.db import db
from app.models.user import User
from app.utils import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/api/profile")
@login_required
def get_profile():
    user = g.current_user
    return jsonify({
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    })


@profile_bp.post("/api/settings/password")
@login_required
def update_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Geçersiz istek."}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Mevcut şifre ve yeni şifre alanları zorunludur."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Yeni şifre en az 6 karakter olmalıdır."}), 400

    user = g.current_user

    if not user.check_password(current_password):
        return jsonify({"error": "Mevcut şifre hatalı."}), 403

    user.password_hash = User.hash_password(new_password)
    db.session.commit()

    return jsonify({"message": "Şifre başarıyla güncellendi."})
