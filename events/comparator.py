from __future__ import annotations
from typing import List, Optional

from .event import Event
from .rules.first_seen import FirstSeenRule
from .rules.ip_changed import IpChangedRule
from .rules.hostname_changed import HostnameChangedRule
from .rules.vendor_discovered import VendorDiscoveredRule
from .rules.device_classified import DeviceClassifiedRule


class SnapshotComparator:
    """
    Сравнивает два Snapshot (старый и новый) и возвращает список событий.
    Не знает о БД, работает только с данными.
    """

    def __init__(self):
        self.rules = [
            FirstSeenRule(),
            IpChangedRule(),
            HostnameChangedRule(),
            VendorDiscoveredRule(),
            DeviceClassifiedRule(),
        ]

    def compare(
        self,
        old_snapshot: Optional[dict],
        new_snapshot: dict,
    ) -> List[Event]:
        """
        Запускает все правила и собирает события.
        
        old_snapshot: предыдущий Snapshot (или None, если это первый)
        new_snapshot: текущий Snapshot
        """
        events: List[Event] = []
        for rule in self.rules:
            event = rule.check(old_snapshot, new_snapshot)
            if event is not None:
                events.append(event)
        return events
