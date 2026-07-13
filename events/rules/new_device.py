from __future__ import annotations
from typing import List
from datetime import datetime

from .base import BaseRule
from events.models import Event, EventType, Severity


class NewDeviceRule(BaseRule):
    """Генерирует событие, если устройство впервые появилось."""

    def detect(self, previous_snapshot: dict | None, current_snapshot: dict) -> List[Event]:
        if previous_snapshot is None:
            # Это первый Snapshot для этого устройства
            return [
                Event(
                    device_id=current_snapshot["device_id"],
                    snapshot_id=current_snapshot["id"],
                    timestamp=datetime.now(),
                    type=EventType.NEW_DEVICE,
                    severity=Severity.INFO,
                    title="Новое устройство",
                    description=f"Устройство {current_snapshot['ip']} ({current_snapshot.get('hostname', 'N/A')}) впервые обнаружено в сети",
                    details=f"IP: {current_snapshot['ip']}, MAC: {current_snapshot.get('mac', 'N/A')}",
                )
            ]
        return []
