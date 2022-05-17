import json

import jwt
import simple_websocket
from sqlalchemy import func

from game.army import Army
from game.game import Game
from game.player import Player
from game.unit import Unit
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
        elif msg["type"] == "attack_request":
            _send(ws, "attack", json.dumps(games[game].get_attacking_squares(is_host, msg["id"])))
        elif msg["type"] == "move_action":
            i = msg["id"]
            pos = tuple(msg["pos"])
            unit = games[game].host.army[i] if is_host else games[game].joiner.army[i]
            if pos in games[game].get_possible_moves(is_host, i):
                unit.position = pos
                unit.activated = True
                games[game].moved_unit = i
                _broadcast(games[game], "game_data", json.dumps(games[game].as_dict))
                _log(games[game], f"{unit.name} (#{i}) moved to {Unit.get_position_as_string(*pos)}.")
            else:
                _send(ws, "error", "Illegal Move")
        elif msg["type"] == "attack_action":
            i = msg["id"]
            pos = tuple(msg["pos"])
            try:
                damage, casualties, killed, idx, target_idx = games[game].attack(pos, i, is_host)
                pname = games[game].host.name if is_host else games[game].joiner.name
                attacker = games[game].host.army[idx] if is_host else games[game].joiner.army[idx]
                defender = games[game].joiner.army[target_idx] if is_host else games[game].host.army[target_idx]
                _log(
                    games[game],
                    f"{pname} attacked {defender.name} (#{target_idx}) with {attacker.name} (#{idx}), resulting in {casualties} casualties ({damage} damage){', killing the unit' if killed else ''}."
                )
                if killed:
                    army = games[game].host.army if not is_host else games[game].joiner.army
                    del army[target_idx]
                _broadcast(games[game], "game_data", json.dumps(games[game].as_dict))
            except Exception as e:
                print("ERROR: " + str(e))
                _send(ws, "error", str(e))


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
        _broadcast(games[game], "game_data", json.dumps(games[game].as_dict))
    return is_host


def _send(ws: simple_websocket.Server, msg_type: str, content: str):
    ws.send(json.dumps({"type": msg_type, "content": content}))


def _broadcast(game: Game, msg_type: str, content: str):
    game.host_ws.send(json.dumps({"type": msg_type, "content": content}))
    game.joiner_ws.send(json.dumps({"type": msg_type, "content": content}))


def _log(game: Game, content: str):
    _broadcast(game, "msg", json.dumps({"type": "log", "content": content}))


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
