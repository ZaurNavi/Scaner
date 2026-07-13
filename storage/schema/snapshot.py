from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .enums import DeviceType

@dataclass(frozen=True)
class Snapshot:
    scan_id: str
    device_id: str
    ip: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    hostname: str = ""
    os: str = ""
    model: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    confidence: int = 0
