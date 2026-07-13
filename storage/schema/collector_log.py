from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .enums import CollectorStatus

@dataclass(frozen=True)
class CollectorLog:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scan_id: str
    collector_name: str
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_ms: float = 0.0
    objects_processed: int = 0
    status: CollectorStatus = CollectorStatus.SUCCESS
    warnings: int = 0
    error_message: str = ""
