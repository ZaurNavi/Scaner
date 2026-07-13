from __future__ import annotations
from typing import List
from datetime import datetime

from .base import BaseRule
from events.models import Event, EventType, Severity


class IpChangedRule(BaseRule):
    """Генерирует событие, если IP изменился."""

    def detect(self, previous_snapshot: dict | None, current_snapshot: dict) -> List[Event]:
        if previous_snapshot is None:
            return []

        old_ip = previous_snapshot["ip"]
        new_ip = current_snapshot["ip"]

        if old_ip != new_ip:
            return [
                Event(
                    device_id=current_snapshot["device_id"],
                    snapshot_id=current_snapshot["id"],
                    timestamp=datetime.now(),
                    type=EventType.IP_CHANGED,
                    severity=Severity.WARNING,
                    title="IP изменился",
                    description=f"Устройство сменило IP-адрес",
                    details=f"Было: {old_ip}, Стало: {new_ip}",
                )
            ]
        return []
