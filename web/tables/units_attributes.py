from web.base import db

units_attributes = db.Table(
    "units_attributes",
    db.Column("unit_id", db.Integer, db.ForeignKey("unit_data.id"), primary_key=True),
    db.Column("attribute_id", db.Integer, db.ForeignKey("attribute.id"), primary_key=True),
)
