from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class FixtureURLContent:
    content: bytes = b""


FixtureURLS = Dict[str, FixtureURLContent]
