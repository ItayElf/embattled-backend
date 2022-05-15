import hashlib
import io
import os.path
import random
from string import printable

import sqlalchemy.exc
from flask import request, jsonify, send_file
from flask_jwt_extended import create_refresh_token, create_access_token, jwt_required, get_jwt_identity
from web import User
from web.base import app, db

SALT_SIZE = 32
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blank_profile.webp"), "rb") as f:
    _blank_profile = f.read()


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if not email or not password:
        return "Missing parameters", 400
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


@app.route("/api/auth/current_user")
@jwt_required()
def auth_current_user():
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first()
    if not user:
        return "No user was found with this token", 404
    return jsonify(user.serialized)


@app.route("/api/auth/profile/<int:idx>")
def auth_profile_pic(idx):
    user = User.query.filter_by(id=idx).first()
    if not user:
        return "", 404
    if user.profile_pic:
        return send_file(io.BytesIO(user.profile_pic), mimetype="image/webp")
    else:
        return send_file(io.BytesIO(_blank_profile), mimetype="image/webp")


@app.route("/api/auth/profile/<name>")
def auth_profile_pic_name(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        return "", 404
    if user.profile_pic:
        return send_file(io.BytesIO(user.profile_pic), mimetype="image/webp")
    else:
        return send_file(io.BytesIO(_blank_profile), mimetype="image/webp")
