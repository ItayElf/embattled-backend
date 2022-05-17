from dataclasses import dataclass, asdict, field

import simple_websocket.ws

from game.attack_arguments import AttackArguments
from game.player import Player
from game.unit import Unit
from web import Mode

position = tuple[int, int]


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

    def get_possible_moves(self, host: bool, idx: int) -> list[position]:
        unit = self.host.army[idx] if host else self.joiner.army[idx]
        return list(set(p[0] for p in self._get_possible_moves(host, unit.speed, unit.position, set())))

    def get_attacking_squares(self, host: bool, idx: int):
        unit = self.host.army[idx] if host else self.joiner.army[idx]
        melee = set(p[0] for p in self._get_attacking_squares(host, 1.5, unit.position, set()))
        range_squares = set()
        for n in self._get_neighbors(unit.position):
            u, is_host = self._unit_at(n)
            if u and is_host != host or not unit.ammunition:
                break
        else:
            range_squares = set(p[0] for p in self._get_attacking_squares(host, unit.range, unit.position, set()))
            range_squares.remove(unit.position)
            for p in melee:
                if p in range_squares:
                    range_squares.remove(p)
        return {
            "melee": list(melee),
            "range": list(range_squares)
        }

    def attack(self, pos: position, idx: int, is_host: bool):
        unit = self.host.army[idx] if is_host else self.joiner.army[idx]
        positions = self.get_attacking_squares(is_host, idx)
        if pos not in positions["melee"] and pos not in positions["range"]:
            raise Exception("Out of range")
        target, host = self._unit_at(pos)
        if not target or host == is_host:
            raise Exception(f"No valid target at {Unit.get_position_as_string(*pos)}")
        ranged = pos in positions["range"]
        charge = unit.activated and not ranged
        adj_enemy = False
        adj_ally = False
        for n in self._get_neighbors(pos):
            u, h = self._unit_at(n)
            if not u:
                continue
            if h == is_host:
                adj_ally = True
            else:
                adj_enemy = True
        flank = not ranged and adj_enemy and not adj_ally
        adv = 0
        if self._tile_at(unit.position) == "w":
            adv -= 1
        if self._tile_at(pos) == "w":
            adv += 1
        args = AttackArguments(ranged, flank, charge, adv)
        d, c = unit.attack(target, args)
        killed = False
        if not target.unit_size or not target.morale:
            target_id, is_h = self._index_of_unit_at(pos)
            army = self.host.army if is_h else self.joiner.army
            del army[target_id]
            killed = True
        return c, d, killed

    def _get_possible_moves(self, host: bool, speed: float, pos: position, moves: set[tuple[position, float]]) -> set[
        tuple[position, float]]:
        if (pos, speed) in moves:
            return moves
        for n in self._get_neighbors(pos):
            cost = self._get_cost_to_move(pos, n, host)
            if cost > speed:
                continue
            self._get_possible_moves(host, speed - cost, n, moves)
            unit_at, is_host = self._unit_at(n)
            if not unit_at:
                moves.add((n, speed - cost))
        return moves

    def _get_attacking_squares(self, host: bool, distance: float, pos: position, squares: set[tuple[position, float]]):
        if (pos, distance) in squares:
            return squares
        for n in self._get_neighbors(pos):
            cost = self._get_cost_to_attack(pos, n)
            if cost > distance:
                continue
            self._get_attacking_squares(host, distance - cost, n, squares)
            squares.add((n, distance - cost))
        return squares

    def _get_cost_to_attack(self, start: position, end: position):
        cost = 1.5 if start[0] != end[0] and start[1] != end[1] else 1
        tile = self._tile_at(end)
        if tile == "r":
            cost *= float("inf")
        return cost  # TODO: handle rocks blocking view

    def _get_cost_to_move(self, start: position, end: position, host: bool) -> float:
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

    def _unit_at(self, pos: position):
        for u in self.host.army.values():
            if u.position == pos:
                return u, True
        for u in self.joiner.army.values():
            if u.position == pos:
                return u, False
        return None, None

    def _index_of_unit_at(self, pos: position):
        for idx in self.host.army:
            if self.host.army[idx].position == pos:
                return idx, True
        for idx in self.joiner.army:
            if self.joiner.army[idx].position == pos:
                return idx, False
        return None, None

    def _tile_at(self, pos: position):
        return self.map[pos[1] * 16 + pos[0]]

    def _get_neighbors(self, pos: position):
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
