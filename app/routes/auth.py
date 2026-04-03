# Login. Kullanıcı burada email ve şifre girer. 
# Eğer doğruysa maine gönderir.

from app.models import User
from app.db import db
from flask import Blueprint, render_template, request, redirect, session, url_for
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
	# Eğer form gönderildiyse
	if request.method == "POST":
		email = request.form.get("email")
		password = request.form.get("password")

		# Şimdilik basit kontrol
		user = User.query.filter_by(email=email).first()
		if user is None:
			return redirect(url_for("auth.register"))

		elif not user.check_password(password):
			return "Şifre yanlış!"
		else:
			session["user"] = user.email
			return redirect(url_for("main.index"))

	# Sayfa ilk açıldığında
	return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		email = request.form.get("email")
		password = request.form.get("password")
		hashed_password = User.hash_password(password)

		user = User.query.filter_by(email=email).first()

		if user is not None:
			return "Bu mail zaten kayıtlı."
		else:
			new_user= User(
				email=email,
				password_hash=hashed_password
			)
			db.session.add(new_user)
			db.session.commit()
			return redirect(url_for("auth.login"))


	return render_template("auth/register.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))
