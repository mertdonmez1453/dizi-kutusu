from functools import wraps
from flask import session, redirect, url_for, g
from app.models.user import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=session["user"]).first()
        if user is None:
            session.pop("user", None)
            return redirect(url_for("auth.login"))

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
