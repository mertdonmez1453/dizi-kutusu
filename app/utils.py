from functools import wraps
from flask import session, redirect, url_for, g, request, jsonify
from app.models.user import User


def paginate(query, serialize_fn, max_per_page=50, default_limit=50):
    """
    Sayfalama isteğe bağlıdır. ?page= parametresi varsa sayfalı format döner,
    yoksa eski düz array formatını korur (geriye uyumluluk).
    """
    page_param = request.args.get("page", type=int)

    if page_param is None:
        items = query.limit(default_limit).all()
        return jsonify([serialize_fn(item) for item in items])

    page = max(1, page_param)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = max(1, min(per_page, max_per_page))

    result = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [serialize_fn(item) for item in result.items],
        "page": result.page,
        "per_page": result.per_page,
        "total": result.total,
        "pages": result.pages
    })


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


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return _unauthorized_response()

        user = User.query.filter_by(email=session["user"]).first()
        if user is None:
            session.pop("user", None)
            return _unauthorized_response()

        if not user.is_admin:
            return jsonify({"error": "Bu işlem için admin yetkisi gerekiyor."}), 403

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
