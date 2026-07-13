from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from .enums import ObservationType
from .source import Source

@dataclass(frozen=True)
class Observation:
    snapshot_id: str
    source: Source
    key: str
    value: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    obs_type: ObservationType = ObservationType.STRING
    unit: str | None = None
    confidence: int = 0
