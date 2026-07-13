from __future__ import annotations
from typing import List
from datetime import datetime

from .base import BaseRule
from events.models import Event, EventType, Severity


class HostnameChangedRule(BaseRule):
    """Генерирует событие, если hostname изменился."""

    def detect(self, previous_snapshot: dict | None, current_snapshot: dict) -> List[Event]:
        if previous_snapshot is None:
            return []

        old_hostname = previous_snapshot.get("hostname") or ""
        new_hostname = current_snapshot.get("hostname") or ""

        if old_hostname != new_hostname and new_hostname:
            return [
                Event(
                    device_id=current_snapshot["device_id"],
                    snapshot_id=current_snapshot["id"],
                    timestamp=datetime.now(),
                    type=EventType.HOSTNAME_CHANGED,
                    severity=Severity.INFO,
                    title="Hostname изменился",
                    description=f"Устройство сменило имя",
                    details=f"Было: {old_hostname or 'N/A'}, Стало: {new_hostname}",
                )
            ]
        return []
