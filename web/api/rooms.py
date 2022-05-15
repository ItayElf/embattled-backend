from flask import jsonify, request

from game.army import Army
from web import Room, Mode
from web.base import app


@app.route("/api/rooms")
def rooms_rooms():
    rooms = Room.query.all()
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
