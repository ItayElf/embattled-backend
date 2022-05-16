from dataclasses import dataclass

from game.unit import Unit


@dataclass
class Player:
    name: str
    rating: int
    army: dict[int, Unit]
    faction: str

    def fix_position(self, board_size: int):
        for unit in self.army.values():
            unit.position = (board_size - unit.position[0] - 1, board_size - unit.position[1] - 1)
