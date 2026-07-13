from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class FirstSeenRule:
    """Если предыдущего Snapshot нет — устройство впервые в сети."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is not None:
            return None

        return Event(
            type=EventType.FIRST_SEEN,
            severity=Severity.INFO,
            title="Новое устройство",
            description=f"Устройство {new_snapshot.get('ip', '?')} впервые обнаружено в сети",
            device_id=new_snapshot.get("device_id", ""),
            old_value="",
            new_value=new_snapshot.get("ip", ""),
            metadata={"device_type": new_snapshot.get("device_type", "UNKNOWN")},
        )
