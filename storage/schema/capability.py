from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from .enums import CapabilityType

@dataclass(frozen=True)
class Capability:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_id: str
    capability: CapabilityType
    confidence: int = 0
