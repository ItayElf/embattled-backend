from web.base import db
from web.tables.units_attributes import units_attributes


class UnitData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False)
    clas = db.Column(db.String, nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    unit_size = db.Column(db.Integer, nullable=False)
    hitpoints = db.Column(db.Integer, nullable=False)
    armor = db.Column(db.Integer, nullable=False)
    morale = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Integer, nullable=False)
    melee_attack = db.Column(db.Integer, nullable=False)
    melee_damage = db.Column(db.Integer, nullable=False)
    charge_bonus = db.Column(db.Integer, nullable=False)
    ammunition = db.Column(db.Integer)
    range = db.Column(db.Integer)
    ranged_attack = db.Column(db.Integer)
    ranged_damage = db.Column(db.Integer)
    attributes = db.relationship("Attribute", secondary=units_attributes, lazy=False,
                                 backref=db.backref("units", lazy=True))
