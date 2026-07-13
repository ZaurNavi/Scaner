from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class IpChangedRule:
    """Если IP изменился — генерирует IP_CHANGED."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is None:
            return None

        old_ip = old_snapshot.get("ip", "")
        new_ip = new_snapshot.get("ip", "")

        if not old_ip or not new_ip or old_ip == new_ip:
            return None

        return Event(
            type=EventType.IP_CHANGED,
            severity=Severity.WARNING,
            title="IP изменился",
            description="Устройство сменило IP-адрес",
            device_id=new_snapshot.get("device_id", ""),
            old_value=old_ip,
            new_value=new_ip,
        )
