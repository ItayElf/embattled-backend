from web.base import db


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    mode_id = db.Column(db.Integer, db.ForeignKey("mode.id"), nullable=False)
    mode = db.relationship("Mode")
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    host = db.relationship("User")
    room_hash = db.Column(db.String, unique=True, nullable=False)

    @property
    def serialized(self):
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode.serialized,
            "host": self.host.serialized,
            "room_hash": self.room_hash,
        }
