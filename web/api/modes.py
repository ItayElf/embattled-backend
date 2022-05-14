from flask import jsonify

from web import Mode
from web.base import app


@app.route("/api/modes")
def modes_modes():
    modes = Mode.query.all()
    return jsonify([m.serialized for m in modes])
