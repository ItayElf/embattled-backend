from dataclasses import dataclass, asdict, field

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
    map: str
    is_host_turn: bool = field(init=False)

    def __post_init__(self):
        self.is_host_turn = True

    @property
    def as_dict(self):
        return {
            "host": asdict(self.host),
            "joiner": asdict(self.joiner),
            "mode": self.mode.serialized,
            "map": self.map,
            "is_host_turn": self.is_host_turn
        }
