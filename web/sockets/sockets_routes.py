import json

import jwt
import simple_websocket
from sqlalchemy import func

from game.army import Army
from game.game import Game
from game.player import Player
from web import User, Room, Mode, Map
from web.base import sockets, app

games: dict[str, Game] = {}


@sockets.route("/sockets/<game>")
def sockets_game(ws, game):
    is_host = _prepare(ws, game)
    while True:
        msg = json.loads(ws.receive())
        print(f"{msg=}")
        if msg["type"] == "move_request":
            _send(ws, "move", json.dumps(games[game].get_possible_moves(is_host, msg["id"])))
        elif msg["type"] == "move_action":
            i = msg["id"]
            pos = tuple(msg["pos"])
            unit = games[game].host.army[i] if is_host else games[game].joiner.army[i]
            if pos in games[game].get_possible_moves(is_host, i):
                unit.position = pos
                unit.activated = True
                _send(ws, "game_data", json.dumps(games[game].as_dict))
            else:
                _send(ws, "error", "Illegal Move")


def _prepare(ws, game):
    user = _get_user(ws)
    room = Room.query.filter_by(room_hash=game).first()
    if not room or (room.host_id != user.id and room.joiner_id != user.id):
        _send(ws, "error", "No room")
    _send(ws, "request", "army")
    army = Army.from_json(json.loads(ws.receive()))
    m = Mode.query.filter_by(id=army.mode_id).first()
    is_host = room.host_id == user.id
    if is_host:
        a, f = army.units_to_dict()
        p = Player(user.name, user.rating, a, f)
        mp = Map.query.filter_by(board_size=m.board_size).order_by(func.random()).first()
        g = Game(p, None, ws, None, m, mp.tiles)
        games[game] = g
    else:
        a, f = army.units_to_dict()
        if games[game].host.faction == f:
            f += " Alt"
        p = Player(user.name, user.rating, a, f)
        p.fix_position(games[game].mode.board_size)
        games[game].joiner = p
        games[game].joiner_ws = ws
    while games[game].joiner is None:
        ...
    if is_host:
        _send(ws, "game_data", json.dumps(games[game].as_dict))
        _send(games[game].joiner_ws, "game_data", json.dumps(games[game].as_dict))
    return is_host


def _send(ws: simple_websocket.Server, msg_type: str, content: str):
    ws.send(json.dumps({"type": msg_type, "content": content}))


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
