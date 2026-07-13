from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .source import Source

@dataclass(frozen=True)
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    source: Source
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration: float = 0.0
    bytes_in: int = 0
    bytes_out: int = 0
    flows: int = 0
