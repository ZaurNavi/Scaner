from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid

from .event_type import EventType, Severity


@dataclass(frozen=True)
class Event:
    """Неизменяемое событие, вычисленное Event Engine."""
    type: EventType
    severity: Severity
    title: str
    description: str
    device_id: str
    snapshot_id: str = ""  # <-- ДОБАВЛЕНО
    old_value: str = ""
    new_value: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
