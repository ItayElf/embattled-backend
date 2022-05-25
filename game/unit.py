from __future__ import annotations

import math
import random
from dataclasses import dataclass

from game.attack_arguments import AttackArguments
from game.attribute import Attribute
from web import UnitData


@dataclass
class Unit:
    name: str
    clas: str
    cost: int
    unit_size_max: int
    unit_size: int
    hitpoints: int
    armor: int
    morale_max: int
    morale: int
    speed: int
    defense: int
    melee_attack: int
    melee_damage: int
    charge_bonus: int
    ammunition_max: int | None
    ammunition: int | None
    range: int | None
    ranged_attack: int | None
    ranged_damage: int | None
    attributes: list[Attribute]
    keywords: list[str]
    position: tuple[int, int]  # position from top left corner
    activated: bool

    @classmethod
    def from_data(cls, unit_data: UnitData):
        """Returns a unit object from datasheet"""
        return cls(unit_data.name, unit_data.clas, unit_data.cost, unit_data.unit_size, unit_data.unit_size,
                   unit_data.hitpoints, unit_data.armor, unit_data.morale, unit_data.morale, unit_data.speed,
                   unit_data.defense, unit_data.melee_attack, unit_data.melee_damage, unit_data.charge_bonus,
                   unit_data.ammunition, unit_data.ammunition, unit_data.range, unit_data.ranged_attack,
                   unit_data.ranged_damage, [Attribute.from_model(a) for a in unit_data.attributes],
                   [a.name for a in unit_data.keywords], (0, 0), False)

    @property
    def is_ranged(self):
        return self.range is not None

    @property
    def visibility(self):
        if self.has_attribute("Alert"):
            return 7
        return 6

    def has_attribute(self, attr: str):
        return any([a.name.lower() == attr.lower() for a in self.attributes])

    def has_keyword(self, keyword: str):
        return any([k.lower() == keyword.lower() for k in self.keywords])

    def get_modifiers_for_attack(self, other: Unit, args: AttackArguments):
        """Returns the modifier of the damage an attack should have"""
        m = 1
        if args.flank:
            m *= 1.25
        if args.charge and not (other.has_attribute("Polearm") and not args.flank):
            m *= (1 + self.charge_bonus / 100)
        power = -1 if args.advantage < 0 else 1 if args.advantage > 0 else 0
        m *= (1 + 0.25 * abs(min(args.advantage, 4))) ** power
        return m

    def get_morale_modifier(self, other: Unit, args: AttackArguments):
        m = 1.5 if args.flank else 1
        if self.has_attribute("Fearsome"):
            m *= 1.5
        return m

    def calc_damage(self, other: Unit, args: AttackArguments):
        """Returns the maximum damage a can do to another"""
        if args.ranged:
            if self.ammunition is None:
                raise ValueError("Unit is not capable of attacking from range")
            elif self.ammunition == 0:
                raise ValueError("Unit is out of ammunition")

        attack_skill = self.ranged_attack if args.ranged else self.melee_attack
        diff = attack_skill - other.defense
        ratio = max((84 + diff * abs(diff)) / 100, .25)
        hits = round(ratio * self.unit_size)
        hits = max(1, hits)  # no less than one hit
        damage = self.ranged_damage if args.ranged else self.melee_damage
        total = (max(damage * (100 - other.armor * 2) / 100, 1)) * hits * self.get_modifiers_for_attack(other, args)
        return total

    def attack(self, other: Unit, args: AttackArguments):
        """Resolve an attack of this unit on 'other' and returns the damage done and casualties"""
        damage = round(self.calc_damage(other, args) * random.uniform(0.85, 1), 2)
        starting_size = other.unit_size
        pool = other.unit_size * other.hitpoints
        pool = max((0, pool - damage))
        other.unit_size = math.ceil(pool / other.hitpoints)
        casualties = starting_size - other.unit_size

        if args.ranged:
            self.ammunition -= 1

        if other.unit_size:
            morale_modifier = self.get_morale_modifier(other, args)
            ratio = casualties / starting_size + 0.5
            other.morale -= casualties * ratio * morale_modifier
            other.morale = max(math.ceil(other.morale), 0)
        return damage, casualties

    @property
    def relative_value(self):
        return int(self.cost * (self.unit_size / self.unit_size_max))

    @staticmethod
    def get_position_as_string(x: int, y: int, board_size: int):
        return f"{chr(65 + x)}{board_size - y}"
