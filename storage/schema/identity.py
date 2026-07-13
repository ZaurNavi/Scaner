from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from .enums import DeviceType

@dataclass(frozen=True)
class Identity:
    device_id: str
    mac: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vendor: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    fingerprint_hash: str = ""
    base_confidence: int = 0
