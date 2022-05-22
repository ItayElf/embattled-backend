import json
import random

import jwt
import simple_websocket
from sqlalchemy import func

from game.army import Army
from game.game import Game
from game.player import Player
from game.unit import Unit
from web import User, Room, Mode, Map
from web.base import sockets, app, db

games: dict[str, Game] = {}


@sockets.route("/sockets/<game>")
def sockets_game(ws: simple_websocket.Server, game):
    is_host = _prepare(ws, game)
    game_obj = games[game]
    while True:
        msg = json.loads(ws.receive())
        print(f"{msg=}")
        if msg["type"] == "move_request":
            _send(ws, "move", json.dumps(game_obj.get_possible_moves(is_host, msg["id"])))
        elif msg["type"] == "attack_request":
            _send(ws, "attack", json.dumps(game_obj.get_attacking_squares(is_host, msg["id"])))
        elif msg["type"] == "move_action":
            i = msg["id"]
            pos = tuple(msg["pos"])
            unit = game_obj.host.army[i] if is_host else game_obj.joiner.army[i]
            if pos in game_obj.get_possible_moves(is_host, i):
                game_obj.last_move = (unit.position, pos)
                unit.position = pos
                unit.activated = True
                game_obj.moved_unit = i
                _send(
                    game_obj.host_ws,
                    "msg",
                    json.dumps(
                        {
                            "type": "log",
                            "content": f"<strong>{unit.name} (#{i})</strong> moved from <strong>{Unit.get_position_as_string(*game_obj.last_move[0]) if game_obj.last_move[0] in game_obj.host_visible else '??'}</strong> to <strong>{Unit.get_position_as_string(*pos) if pos in game_obj.host_visible else '??'}</strong>."
                        }
                    )
                )
                _send(
                    game_obj.joiner_ws,
                    "msg",
                    json.dumps(
                        {
                            "type": "log",
                            "content": f"<strong>{unit.name} (#{i})</strong> moved from <strong>{Unit.get_position_as_string(*game_obj.last_move[0]) if game_obj.last_move[0] in game_obj.joiner_visible else '??'}</strong> to <strong>{Unit.get_position_as_string(*pos) if pos in game_obj.joiner_visible else '??'}</strong>."
                        }
                    )
                )
                game_obj.update_visibility()
                _broadcast(game_obj, "game_data", json.dumps(game_obj.as_dict))
            else:
                _send(ws, "error", "Illegal Move")
        elif msg["type"] == "attack_action":
            i = msg["id"]
            pos = tuple(msg["pos"])
            try:
                damage, casualties, killed, idx, target_idx = game_obj.attack(pos, i, is_host)
                pname = game_obj.host.name if is_host else game_obj.joiner.name
                attacker = game_obj.host.army[idx] if is_host else game_obj.joiner.army[idx]
                defender = game_obj.joiner.army[target_idx] if is_host else game_obj.host.army[target_idx]
                _log(
                    game_obj,
                    f"<strong>{pname}</strong> attacked <strong>{defender.name} (#{target_idx})</strong> with <strong>{attacker.name} (#{idx})</strong>, resulting in <strong>{casualties} casualties</strong> ({damage} damage){', <strong>killing the unit</strong>' if killed else ''}."
                )
                if killed:
                    army = game_obj.host.army if not is_host else game_obj.joiner.army
                    del army[target_idx]
                if _pass_turn(game_obj, game):
                    ...
                _broadcast(game_obj, "game_data", json.dumps(game_obj.as_dict))
            except ValueError as e:
                print("ERROR: " + str(e))
                _send(ws, "error", str(e))
        elif msg["type"] == "halt":
            i = msg["id"]
            if i != -1:
                game_obj.current_player.army[i].activated = True
                _log(game_obj, f"<strong>{game_obj.current_player.army[i].name} (#{i})</strong> halted.")
            if _pass_turn(game_obj, game):
                ...
            _broadcast(game_obj, "game_data", json.dumps(game_obj.as_dict))
        elif msg["type"] == "close":
            break
    print(f"LOGGED OUT: {is_host=}")


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
        tiles = mp.tiles[::random.choice([-1, 1])]
        g = Game(p, None, ws, None, m, tiles)
        games[game] = g
        games[game].update_visibility(True)
    else:
        a, f = army.units_to_dict()
        if games[game].host.faction == f:
            f += " Alt"
        p = Player(user.name, user.rating, a, f)
        p.fix_position(games[game].mode.board_size)
        games[game].joiner = p
        games[game].joiner_ws = ws
        games[game].update_visibility(False)
    while games[game].joiner is None:
        ...
    if is_host:
        _broadcast(games[game], "game_data", json.dumps(games[game].as_dict))
        _log(games[game],
             f"<strong>Game started between {games[game].host.name} ({games[game].host.rating}) and {games[game].joiner.name} ({games[game].joiner.rating}).</strong><br/>"
             f"<strong>Mode:</strong> {games[game].mode.name} ({games[game].mode.points}P).<br/>"
             f"<strong>Win Condition:</strong> {games[game].mode.win_condition}.")
        _broadcast(games[game], "msg", json.dumps({"type": "turn", "turn": games[game].turn_counter}))
    return is_host


def _pass_turn(game: Game, room_hash: str):
    is_win, winner, loser = game.check_win()
    if is_win:
        _handle_win(game, winner, loser, room_hash)
        # game.host_ws.close()
        # game.joiner_ws.close()
        return is_win
    if game.pass_round():
        _broadcast(game, "msg", json.dumps({"type": "turn", "turn": game.turn_counter}))
    return is_win


def _handle_win(game: Game, winner: Player, loser: Player, room_hash: str):
    ra = winner.rating
    rb = loser.rating
    nra = winner.calc_new_rating(rb, True)
    nrb = loser.calc_new_rating(ra, False)
    w = User.query.filter_by(name=winner.name).first()
    w.rating = nra
    l = User.query.filter_by(name=loser.name).first()
    l.rating = nrb
    _log(
        game,
        f"<strong>{winner.name} defeated {loser.name}.</strong><br/>"
        f"<strong>{winner.name}'s new rating is <strong>{nra}</strong> (+{nra - ra})<br/>"
        f"<strong>{loser.name}'s new rating is <strong>{nrb}</strong> ({nrb - rb})<br/>"
    )
    _broadcast(game, "game_data", json.dumps(game.as_dict))
    room = Room.query.filter_by(room_hash=room_hash).first()
    del games[room.room_hash]
    db.session.delete(room)
    db.session.commit()


def _send(ws: simple_websocket.Server, msg_type: str, content: str):
    ws.send(json.dumps({"type": msg_type, "content": content}))


def _broadcast(game: Game, msg_type: str, content: str):
    if game.host_ws and game.joiner_ws.connected:
        game.host_ws.send(json.dumps({"type": msg_type, "content": content}))
    if game.joiner_ws and game.joiner_ws.connected:
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
