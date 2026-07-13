from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .enums import DeviceStatus

@dataclass(frozen=True)
class Device:
    mac: str  # <-- Сначала обязательные поля
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: DeviceStatus = DeviceStatus.ACTIVE
