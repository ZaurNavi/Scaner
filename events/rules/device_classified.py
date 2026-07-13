from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class DeviceClassifiedRule:
    """Если тип устройства изменился (особенно UNKNOWN -> что-то) — генерирует DEVICE_CLASSIFIED."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is None:
            return None

        old_type = (old_snapshot.get("device_type") or "UNKNOWN").upper()
        new_type = (new_snapshot.get("device_type") or "UNKNOWN").upper()

        # Пропускаем, если тип не изменился
        if old_type == new_type:
            return None

        # Пропускаем, если новый тип — UNKNOWN (деградация)
        if new_type == "UNKNOWN":
            return None

        # Определяем серьёзность: UNKNOWN -> что-то важнее, чем X -> Y
        severity = Severity.INFO
        if old_type == "UNKNOWN":
            severity = Severity.INFO  # Первая классификация
        else:
            severity = Severity.WARNING  # Переклассификация

        return Event(
            type=EventType.DEVICE_CLASSIFIED,
            severity=severity,
            title="Тип устройства изменился",
            description="Устройство переклассифицировано",
            device_id=new_snapshot.get("device_id", ""),
            old_value=old_type,
            new_value=new_type,
        )
