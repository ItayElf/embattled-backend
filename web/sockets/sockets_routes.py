import json

import jwt

from game.army import Army
from game.game import Game
from game.player import Player
from web import User, Room, Mode
from web.base import sockets, app

games: dict[str, Game] = {}


@sockets.route("/sockets/<game>")
def sockets_game(ws, game):
    _prepare(ws, game)
    while True:
        msg = ws.receive()


def _prepare(ws, game):
    user = _get_user(ws)
    room = Room.query.filter_by(room_hash=game).first()
    if not room or (room.host_id != user.id and room.joiner_id != user.id):
        ws.send(json.dumps({"type": "error", "content": "No room"}))
    ws.send(json.dumps({"type": "request", "content": "army"}))
    army = Army.from_json(json.loads(ws.receive()))
    m = Mode.query.filter_by(id=army.mode_id).first()
    host = room.host_id == user.id
    if host:
        p = Player(user.name, user.rating, army.units_to_dict())
        g = Game(p, None, ws, None, m)
        games[game] = g
    else:
        p = Player(user.name, user.rating, army.units_to_dict())
        games[game].joiner = p
        games[game].joiner_ws = ws


def _get_user(ws):
    access_token = ws.receive()
    user = None
    while user is None:
        try:
            identity = jwt.decode(access_token, app.config["JWT_SECRET_KEY"], algorithms=['HS256'])["sub"]
            user = User.query.filter_by(email=identity).first()
        except jwt.exceptions.ExpiredSignatureError:
            ws.send(json.dumps({"type": "error", "content": "Invalid Token"}))
    return user
