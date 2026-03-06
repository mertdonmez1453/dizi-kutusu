from app import create_app
from app.db import db
from app.models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(users)

print(app.config["SQLALCHEMY_DATABASE_URI"])