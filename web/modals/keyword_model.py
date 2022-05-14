from web.base import db


class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    @property
    def serialized(self):
        return {"id": self.id, "name": self.name}
