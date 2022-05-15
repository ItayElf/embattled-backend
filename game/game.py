from dataclasses import dataclass

import simple_websocket.ws

from game.player import Player
from web import Mode


@dataclass
class Game:
    host: Player
    joiner: Player | None
    host_ws: simple_websocket.ws.Server
    joiner_ws: simple_websocket.ws.Server | None
    mode: Mode
