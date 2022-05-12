from web.base import db

units_attributes = db.Table(
    "units_keywords",
    db.Column("unit_id", db.Integer, db.ForeignKey("unit_data.id"), primary_key=True),
    db.Column("keyword_id", db.Integer, db.ForeignKey("keyword.id"), primary_key=True),
)
