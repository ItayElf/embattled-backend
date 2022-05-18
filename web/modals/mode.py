from sqlalchemy.inspection import inspect

from web.base import db


class Mode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    board_size = db.Column(db.Integer, nullable=False)
    win_condition = db.Column(db.String, nullable=False)

    @property
    def serialized(self):
        keys = list(inspect(self).attrs.keys())
        return {c: getattr(self, c) for c in keys}
