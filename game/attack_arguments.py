from dataclasses import dataclass


@dataclass(frozen=True)
class AttackArguments:
    ranged: bool
    flank: bool
    charge: bool
