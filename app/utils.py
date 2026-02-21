from functools import wraps
from flask import session, redirect, url_for, g, request, jsonify
from app.models.user import User


def _is_api_request():
    return request.path.startswith("/api/") or request.is_json


def _unauthorized_response():
    if _is_api_request():
        return jsonify({"error": "Oturum açmanız gerekiyor."}), 401
    return redirect(url_for("auth.login"))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return _unauthorized_response()

        user = User.query.filter_by(email=session["user"]).first()
        if user is None:
            session.pop("user", None)
            return _unauthorized_response()

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
