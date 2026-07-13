from __future__ import annotations
from typing import List
from datetime import datetime

from .base import BaseRule
from events.models import Event, EventType, Severity


class VendorChangedRule(BaseRule):
    """Генерирует событие, если Vendor изменился."""

    def detect(self, previous_snapshot: dict | None, current_snapshot: dict) -> List[Event]:
        if previous_snapshot is None:
            return []

        # Vendor хранится в Observation, но для простоты сравним device_type
        old_type = previous_snapshot.get("device_type") or "UNKNOWN"
        new_type = current_snapshot.get("device_type") or "UNKNOWN"

        if old_type != new_type and new_type != "UNKNOWN":
            return [
                Event(
                    device_id=current_snapshot["device_id"],
                    snapshot_id=current_snapshot["id"],
                    timestamp=datetime.now(),
                    type=EventType.DEVICE_TYPE_CHANGED,
                    severity=Severity.INFO,
                    title="Тип устройства изменился",
                    description=f"Устройство переклассифицировано",
                    details=f"Было: {old_type}, Стало: {new_type}",
                )
            ]
        return []
