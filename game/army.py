from dataclasses import dataclass, asdict

from game.unit import Unit
from web import Mode, UnitData


@dataclass
class SimpleUnit:
    position: list[int, int]
    name: str
    faction: str
    cost: int
    clas: str


@dataclass
class Army:
    name: str
    mode_id: int
    units: list[SimpleUnit]

    @classmethod
    def from_json(cls, json: dict[str, ...]):
        return cls(json["name"], json["mode"]["id"],
                   [SimpleUnit(u["position"], u["name"], u["faction"], u["cost"], u["clas"]) for u in json["units"]])

    @classmethod
    def from_export(cls, export: str):
        lines = [l for l in export.split("\n") if l]
        army_name = lines[0]
        mn, mp, ms = lines[1].split("|")
        m = Mode.query.filter_by(name=mn, points=int(mp), board_size=ms).first()
        if not m:
            raise ValueError(f"No mode with name {mn}, {mp} points and board size {ms} was found")
        lines = lines[2:]
        units = []
        for name, pos in [l.split("|") for l in lines]:
            u = UnitData.query.filter_by(name=name).first()
            if not u:
                raise ValueError(f"No unit named {name} was found")
            x, y = ord(pos[0]) - 65, int(pos[1:])
            units.append(SimpleUnit([x, y], name, u.faction, u.cost, u.clas))
        return cls(army_name, m.id, units)

    def validate(self, mode: Mode):
        lst = []
        cost = 0
        positions = set()
        factions = set()
        for unit in self.units:
            u: UnitData = UnitData.query.filter_by(name=unit.name).first()
            if not u:
                lst.append(f"'{unit.name}' is not a valid unit.")
            else:
                cost += u.cost
                if u.faction:
                    factions.add(u.faction)
            if unit.position[0] < 0 or unit.position[0] >= mode.board_size or unit.position[1] >= mode.board_size or \
                    unit.position[
                        1] < mode.board_size * 3 / 4:
                lst.append(
                    f"'{unit.name}' is positioned at {Unit.get_position_as_string(*unit.position, mode.board_size)}, which is out of bounds.")
            else:
                t = tuple(unit.position)
                if t in positions:
                    lst.append(
                        f"'{unit.name}' is positioned at {Unit.get_position_as_string(*unit.position, mode.board_size)}, which is already occupied.")
                positions.add(tuple(unit.position))
        if cost > mode.points:
            lst.append(f"Your army is worth {cost} points, but only {mode.points} are allowed.")
        if len(factions) > 1:
            lst.append(f"You have too many factions in your army: {','.join(factions)}.")
        if not self.units:
            lst.append("This army has no units.")
        return lst

    def units_to_dict(self):
        d = {}
        factions = set()
        for i, unit in enumerate(self.units):
            unit_data = UnitData.query.filter_by(name=unit.name).first()
            if unit_data.faction:
                factions.add(unit_data.faction)
            d[i + 1] = Unit.from_data(unit_data)
            d[i + 1].position = tuple(unit.position)
        faction = list(factions)[0] if len(factions) > 0 else "Mercenaries"
        return d, faction

    @property
    def as_export(self):
        m = Mode.query.filter_by(id=self.mode_id).first()
        return {
            "name": self.name,
            "mode": m.serialized,
            "units": [asdict(u) for u in self.units]
        }
