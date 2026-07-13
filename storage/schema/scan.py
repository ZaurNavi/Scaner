from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .enums import ScanStatus

@dataclass(frozen=True)
class Scan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    collector_version: str = ""
    duration_ms: float = 0.0
    devices_found: int = 0
    status: ScanStatus = ScanStatus.SUCCESS
