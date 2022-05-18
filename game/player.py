from dataclasses import dataclass, field

from game.unit import Unit


@dataclass
class Player:
    name: str
    rating: int
    army: dict[int, Unit]
    faction: str
    original_value: int = field(init=False)

    def __post_init__(self):
        self.original_value = sum([u.cost for u in self.army.values()])

    @property
    def relative_cost(self):
        return sum([u.relative_value for u in self.army.values()])

    def fix_position(self, board_size: int):
        for unit in self.army.values():
            unit.position = (board_size - unit.position[0] - 1, board_size - unit.position[1] - 1)
