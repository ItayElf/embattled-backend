from web.base import db


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board_size = db.Column(db.Integer, nullable=False)
    tiles = db.Column(db.String, nullable=False)

# g - grass
# w - water
# r - rock
# f - forest
