from dataclasses import dataclass, asdict

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

    @property
    def as_dict(self):
        return {
            "host": asdict(self.host),
            "joiner": asdict(self.joiner),
            "mode": self.mode.serialized
        }
