import hashlib
import random
from string import printable

import sqlalchemy.exc
from flask import request, jsonify
from flask_jwt_extended import create_refresh_token, create_access_token, jwt_required, get_jwt_identity
from web import User
from web.base import app, db

SALT_SIZE = 32


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = User.query.filter_by(email=email).first()
    salt = user.salt
    if hashlib.md5(password.encode() + salt.encode()).hexdigest() == user.password_hash:
        refresh = create_refresh_token(identity=email)
        access = create_access_token(identity=email)
        return jsonify(access_token=access, refresh_token=refresh)
    return "Invalid credentials", 401


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    email = request.json.get("email", None)
    name = request.json.get("name", None)
    password = request.json.get("password", None)
    if not email or not password or not name:
        return "Missing parameters", 400
    salt = "".join(random.choices(printable, k=SALT_SIZE))
    password = hashlib.md5(password.encode() + salt.encode()).hexdigest()
    user = User(email=email, name=name, password_hash=password, salt=salt, profile_pic=None)
    try:
        db.session.add(user)
        db.session.commit()
        refresh = create_refresh_token(identity=email)
        access = create_access_token(identity=email)
        return jsonify(access_token=access, refresh_token=refresh)
    except sqlalchemy.exc.IntegrityError as e:
        if "user.name" in str(e):
            return "Username is already taken", 400
        return "A user with this email already exists.", 400


@app.route("/api/auth/refresh")
@jwt_required(refresh=True)
def auth_refresh():
    identity = get_jwt_identity()
    token = create_access_token(identity=identity)
    return jsonify(access_token=token)
