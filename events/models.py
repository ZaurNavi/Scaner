from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class EventType(str, Enum):
    NEW_DEVICE = "NEW_DEVICE"
    IP_CHANGED = "IP_CHANGED"
    HOSTNAME_CHANGED = "HOSTNAME_CHANGED"
    VENDOR_CHANGED = "VENDOR_CHANGED"
    MODEL_CHANGED = "MODEL_CHANGED"
    DEVICE_TYPE_CHANGED = "DEVICE_TYPE_CHANGED"
    FIRST_SEEN = "FIRST_SEEN"
    LAST_SEEN = "LAST_SEEN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CONFIDENCE_CHANGED = "CONFIDENCE_CHANGED"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ALERT = "ALERT"


@dataclass(frozen=True)
class Event:
    """Неизменяемое событие, генерируемое Event Engine."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = ""
    snapshot_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    type: EventType = EventType.NEW_DEVICE
    severity: Severity = Severity.INFO
    title: str = ""
    description: str = ""
    details: str = ""
    acknowledged: bool = False
