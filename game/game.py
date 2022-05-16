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
    moved_unit: int | None = field(init=False)

    def __post_init__(self):
        self.is_host_turn = True
        self.moved_unit = None

    def get_possible_moves(self, host: bool, idx: int) -> list[tuple[int, int]]:
        unit = self.host.army[idx] if host else self.joiner.army[idx]
        return list(self._get_possible_moves(host, unit.speed, unit.position, set()))

    def _get_possible_moves(self, host: bool, speed: float, pos: tuple[int, int], moves: set[tuple[int, int]]) -> set[
        tuple[int, int]]:
        for n in self._get_neighbors(pos):
            cost = self._get_cost_to_move(pos, n, host)
            if cost > speed:
                continue
            unit_at, is_host = self._unit_at(n)
            if not unit_at:
                moves.add(n)
            self._get_possible_moves(host, speed - cost, n, moves)
        return moves

    def _get_cost_to_move(self, start: tuple[int, int], end: tuple[int, int], host: bool) -> float:
        cost = 1.5 if start[0] != end[0] and start[1] != end[1] else 1
        tile = self._tile_at(end)
        if tile == "w":
            cost *= 2
        elif tile == "r":
            cost *= float("inf")
        unit, is_host = self._unit_at(end)
        if unit and is_host != host:
            cost *= float("inf")
        return cost  # TODO: prevent movement between two diagonal enemies

    def _unit_at(self, pos: tuple[int, int]):
        for u in self.host.army.values():
            if u.position == pos:
                return u, True
        for u in self.joiner.army.values():
            if u.position == pos:
                return u, False
        return None, None

    def _tile_at(self, pos: tuple[int, int]):
        return self.map[pos[1] * 16 + pos[0]]

    def _get_neighbors(self, pos: tuple[int, int]):
        s = set()
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                x = pos[0] + i
                y = pos[1] + j
                if -1 < x < self.mode.board_size and -1 < y < self.mode.board_size:
                    s.add((x, y))
        s.remove(pos)
        return s

    @property
    def as_dict(self):
        return {
            "host": asdict(self.host),
            "joiner": asdict(self.joiner),
            "mode": self.mode.serialized,
            "map": self.map,
            "is_host_turn": self.is_host_turn,
            "moved_unit": self.moved_unit,
        }
