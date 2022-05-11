from dataclasses import dataclass

import web


@dataclass(frozen=True)
class Attribute:
    name: str
    description: str

    @classmethod
    def from_model(cls, attribute: web.Attribute):
        """Returns a dataclass from a model"""
        return cls(attribute.name, attribute.description)
