from __future__ import annotations
from typing import Optional

from ..event import Event
from ..event_type import EventType, Severity


class VendorDiscoveredRule:
    """Если Vendor был Unknown, а стал известен."""

    def check(self, old_snapshot: Optional[dict], new_snapshot: dict) -> Optional[Event]:
        if old_snapshot is None:
            return None

        old_vendor = (old_snapshot.get("vendor") or "").strip()
        new_vendor = (new_snapshot.get("vendor") or "").strip()

        def is_unknown(v: str) -> bool:
            return not v or v.lower() == "unknown"

        if is_unknown(old_vendor) and not is_unknown(new_vendor):
            return Event(
                type=EventType.VENDOR_DISCOVERED,
                severity=Severity.INFO,
                title="Производитель определён",
                description=f"Устройство идентифицировано как {new_vendor}",
                device_id=new_snapshot.get("device_id", ""),
                snapshot_id=new_snapshot.get("id", ""),  # <-- ДОБАВЛЕНО
                old_value=old_vendor or "Unknown",
                new_value=new_vendor,
            )

        return None
