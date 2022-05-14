from web.base import db


class Attribute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False)

    @property
    def serialized(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }
