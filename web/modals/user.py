from web.base import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    salt = db.Column(db.String, nullable=False)
    profile_pic = db.Column(db.LargeBinary, nullable=True)
