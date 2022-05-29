import math

from flask import jsonify, request

from game.attack_arguments import AttackArguments
from game.unit import Unit
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
def units_unit_by_name(name):
    unit = UnitData.query.filter(UnitData.name.ilike(name)).first()
    if not unit:
        return f"No unit with name {name} was found", 404
    return jsonify(unit.serialized)


@app.route("/api/damage_calc")
def units_damage_calc():
    attacker_name = request.args.get("attacker", None)
    defender_name = request.args.get("defender", None)
    if not attacker_name or not defender_name:
        return "Missing Parameters", 400
    attacker = UnitData.query.filter_by(name=attacker_name).first()
    defender = UnitData.query.filter_by(name=defender_name).first()
    if not attacker:
        return f"No unit named {attacker_name}", 404
    if not defender:
        return f"No unit named {defender_name}", 404
    attacker_size = int(request.args.get("attacker_size", str(attacker.unit_size)))
    defender_size = int(request.args.get("defender_size", str(defender.unit_size)))
    ranged = bool(int(request.args.get("ranged", "0")))
    flank = bool(int(request.args.get("flank", "0")))
    charge = bool(int(request.args.get("charge", "0")))
    advantage = int(request.args.get("advantage", "0"))
    args = AttackArguments(ranged, flank, charge, advantage)
    attacker = Unit.from_data(attacker)
    attacker.unit_size = attacker_size
    defender.unit_size = defender_size
    defender = Unit.from_data(defender)
    d = attacker.calc_damage(defender, args)
    return jsonify(
        {
            "max_damage": d,
            "min_damage": d * 0.85,
            "avg_damage": d * 0.925,
            "max_casualties": int(d / defender.hitpoints),
            "min_casualties": int(d * 0.85 / defender.hitpoints),
            "avg_casualties": int(d * 0.925 / defender.hitpoints),
            "min_turns_to_kill": math.ceil(defender.unit_size / int(d / defender.hitpoints)),
            "max_turns_to_kill": math.ceil(defender.unit_size / int(d * 0.85 / defender.hitpoints))
        }
    )
