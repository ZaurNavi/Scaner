from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class DeviceClassifiedRule:
    """Если тип устройства изменился."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is None:
            return None

        old_type = (old_snapshot.get("device_type") or "UNKNOWN").upper()
        new_type = (new_snapshot.get("device_type") or "UNKNOWN").upper()

        if old_type == new_type or new_type == "UNKNOWN":
            return None

        severity = Severity.INFO if old_type == "UNKNOWN" else Severity.WARNING

        return Event(
            type=EventType.DEVICE_CLASSIFIED,
            severity=severity,
            title="Тип устройства изменился",
            description="Устройство переклассифицировано",
            device_id=new_snapshot.get("device_id", ""),
            snapshot_id=new_snapshot.get("id", ""),  # <-- ДОБАВЛЕНО
            old_value=old_type,
            new_value=new_type,
        )
