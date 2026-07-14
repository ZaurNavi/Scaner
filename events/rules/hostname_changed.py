from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class HostnameChangedRule:
    """Если hostname изменился — генерирует HOSTNAME_CHANGED."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is None:
            return None

        old_hostname = old_snapshot.get("hostname") or ""
        new_hostname = new_snapshot.get("hostname") or ""

        if old_hostname == new_hostname or not new_hostname:
            return None

        return Event(
            type=EventType.HOSTNAME_CHANGED,
            severity=Severity.INFO,
            title="Hostname изменился",
            description="Устройство сменило имя",
            device_id=new_snapshot.get("device_id", ""),
            snapshot_id=new_snapshot.get("id", ""),  # <-- ДОБАВЛЕНО
            old_value=old_hostname,
            new_value=new_hostname,
        )
