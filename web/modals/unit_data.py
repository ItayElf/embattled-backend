from sqlalchemy.inspection import inspect

from web.base import db
from web.tables import units_keywords, units_attributes


class UnitData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False)
    faction = db.Column(db.String)
    clas = db.Column(db.String, nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    unit_size = db.Column(db.Integer, nullable=False)
    hitpoints = db.Column(db.Integer, nullable=False)
    armor = db.Column(db.Integer, nullable=False)
    morale = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
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
    keywords = db.relationship("Keyword", secondary=units_keywords, lazy=False, backref=db.backref("units", lazy=True))

    @property
    def serialized(self):
        keys = list(inspect(self).attrs.keys())
        keys.remove("attributes")
        keys.remove("keywords")
        return {
            **{c: getattr(self, c) for c in keys},
            "attributes": [a.serailized for a in self.attributes],
            "keywords": [k.serialized for k in self.keywords]
        }
