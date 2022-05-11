from dataclasses import dataclass

from game.unit import Unit


@dataclass
class Player:
    name: str
    rating: int
    army: dict[int, Unit]
