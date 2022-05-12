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

    @classmethod
    def from_data(cls, unit_data: UnitData):
        """Returns a unit object from datasheet"""
        return cls(unit_data.name, unit_data.clas, unit_data.unit_size, unit_data.unit_size,
                   unit_data.hitpoints, unit_data.armor, unit_data.morale, unit_data.morale, unit_data.speed,
                   unit_data.defense, unit_data.melee_attack, unit_data.melee_damage, unit_data.charge_bonus,
                   unit_data.ammunition, unit_data.ammunition, unit_data.range, unit_data.ranged_attack,
                   unit_data.ranged_damage, [Attribute.from_model(a) for a in unit_data.attributes],
                   [a.name for a in unit_data.keywords])

    @property
    def is_ranged(self):
        return self.range is not None

    def get_modifiers_for_attack(self, other: Unit, args: AttackArguments):
        """Returns the modifier of the damage an attack should have"""
        m = 1
        if args.flank:
            m *= 1.25
        if args.charge:
            m *= (1 + self.charge_bonus / 100)
        return m

    def calc_damage(self, other: Unit, args: AttackArguments):
        """Returns the maximum damage a can do to another"""
        if args.ranged:
            if self.ammunition is None:
                raise ValueError("Unit is not capable of attacking from range")
            elif self.ammunition == 0:
                raise ValueError("Unit is out of ammunition")

        attack_skill = self.ranged_attack if args.ranged else self.melee_attack
        ratio = min((1, attack_skill / other.defense))
        hits = math.ceil(ratio * self.unit_size)
        hits = min(self.unit_size, min(1, hits))  # no less than one hit, no more hits than the unit size
        damage = self.ranged_damage if args.ranged else self.melee_damage
        total = ((damage * damage) / (2 * other.armor)) * hits * self.get_modifiers_for_attack(other, args)
        return round(total, 2)

    def attack(self, other: Unit, args: AttackArguments):
        """Resolve an attack of this unit on 'other' and returns the damage done and casualties"""
        damage = self.calc_damage(other, args) * random.uniform(0.85, 1)
        starting_size = other.unit_size
        pool = other.unit_size * other.hitpoints
        pool = max((0, pool - damage))
        other.unit_size = math.ceil(pool / other.unit_size)
        casualties = starting_size - other.unit_size

        if args.ranged:
            self.ammunition -= 1

        if other.unit_size:
            morale_modifier = 1.5 if args.flank else 1
            ratio = casualties / starting_size + 0.5
            other.morale -= casualties * ratio * morale_modifier
            other.morale = max(math.ceil(other.morale), 0)
        return damage, casualties