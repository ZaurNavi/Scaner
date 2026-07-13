from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from .source import Source

@dataclass(frozen=True)
class Evidence:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_id: str
    description: str
    contribution: int
    source: Source
    details: str = ""
