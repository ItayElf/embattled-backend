from flask import jsonify

from web import Room
from web.base import app


@app.route("/api/rooms")
def rooms_rooms():
    rooms = Room.query.all()
    return jsonify([r.serialized for r in rooms])
