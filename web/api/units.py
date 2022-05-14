from flask import jsonify

from web import UnitData
from web.base import app


@app.route("/api/units")
def units_units():
    units = UnitData.query.all()
    return jsonify([u.serialized for u in units])


@app.route("/api/unit/<int:idx>")
def units_unit_by_id(idx):
    unit = UnitData.query.filter_by(id=idx).first()
    if not unit:
        return f"No unit with id {idx} was found", 404
    return jsonify(unit.serialized)


@app.route("/api/unit/<name>")
def unit_by_name(name):
    unit = UnitData.query.filter(UnitData.name.ilike(name)).first()
    if not unit:
        return f"No unit with name {name} was found", 404
    return jsonify(unit.serialized)
