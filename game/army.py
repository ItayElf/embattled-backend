from dataclasses import dataclass

from game.unit import Unit
from web import Mode, UnitData


@dataclass
class SimpleUnit:
    position: list[int, int]
    name: str


@dataclass
class Army:
    name: str
    mode_id: int
    units: list[SimpleUnit]

    @classmethod
    def from_json(cls, json: dict[str, ...]):
        return cls(json["name"], json["mode"]["id"], [SimpleUnit(u["position"], u["name"]) for u in json["units"]])

    def validate(self, mode: Mode):
        lst = []
        cost = 0
        positions = set()
        for unit in self.units:
            u: UnitData = UnitData.query.filter_by(name=unit.name).first()
            if not u:
                lst.append(f"'{unit.name}' is not a valid unit.")
            else:
                cost += u.cost
            if unit.position[0] < 0 or unit.position[0] > mode.board_size or unit.position[1] < 0 or unit.position[
                1] > mode.board_size / 4:
                lst.append(
                    f"'{unit.name}' is positioned at {Unit.get_position_as_string(*unit.position)}, which is out of bounds.")
            else:
                t = tuple(unit.position)
                if t in positions:
                    lst.append(
                        f"'{unit.name}' is positioned at {Unit.get_position_as_string(*unit.position)}, which is already occupied")
                positions.add(tuple(unit.position))
        if cost > mode.points:
            lst.append(f"Your army is worth {cost} points, but only {mode.points} are allowed.")
        return lst

    def units_to_dict(self):
        d = {}
        for i, unit in enumerate(self.units):
            d[i] = Unit.from_data(UnitData.query.filter_by(name=unit.name).first())
        return d
