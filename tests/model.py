from typing import Dict
from dataclasses import dataclass

@dataclass(frozen=True)
class FixtureURLContent:
    content: bytes = b""

FixtureURLS = Dict[str, FixtureURLContent]
