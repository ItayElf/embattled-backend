import hashlib

import sqlalchemy.exc
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from game.army import Army
from web import Room, Mode, User
from web.base import app, db


@app.route("/api/rooms")
def rooms_rooms():
    rooms = Room.query.filter_by(joiner_id=None).all()
    return jsonify([r.serialized for r in rooms])


@app.route("/api/rooms/validate_army", methods=["POST"])
def rooms_validate_army():
    army = request.json.get("army", None)
    mode_id = request.json.get("mode_id", None)
    if not army or not mode_id:
        return "Missing parameters", 400
    mode = Mode.query.filter_by(id=mode_id).first()
    if not mode:
        return "Invalid mode", 404
    army = Army.from_json(army)
    lst = army.validate(mode)
    res = jsonify(lst)
    res.status_code = 406 if lst else 200
    return res


@app.route("/api/rooms/host", methods=["POST"])
@jwt_required()
def rooms_host():
    name = request.json.get("name", None)
    mode_id = request.json.get("mode_id", None)
    if not name or not mode_id:
        return "Missing parameters", 400
    mode = Mode.query.filter_by(id=mode_id).first()
    if not mode:
        return "Invalid mode", 404
    identity = get_jwt_identity()
    u: User = User.query.filter_by(email=identity).first()
    if not u:
        return f"No user with email {identity} was found"
    room_hash = hashlib.md5((name + mode.name + u.name).encode()).hexdigest()
    r = Room(name=name, mode_id=mode.id, host_id=u.id, room_hash=room_hash)
    try:
        db.session.add(r)
        db.session.commit()
        return room_hash, 200
    except sqlalchemy.exc.IntegrityError:
        return f"Room name '{name}' is taken.", 400
