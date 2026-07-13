from __future__ import annotations
from typing import List

from events.models import Event
from events.repository import EventRepository
from events.rules import NewDeviceRule, IpChangedRule, HostnameChangedRule, VendorChangedRule


class EventEngine:
    """
    Event Engine — модуль, который анализирует историю и генерирует события.
    Работает только с БД, не с сетью.
    """

    def __init__(self, event_repository: EventRepository):
        self.event_repo = event_repository
        self.rules = [
            NewDeviceRule(),
            IpChangedRule(),
            HostnameChangedRule(),
            VendorChangedRule(),
        ]

    def analyze_snapshot(self, current_snapshot: dict) -> List[Event]:
        """
        Анализирует текущий Snapshot, сравнивая с предыдущим.
        Возвращает список сгенерированных событий.
        """
        device_id = current_snapshot.get("device_id")
        snapshot_id = current_snapshot.get("id")

        if not device_id or not snapshot_id:
            return []

        # Получаем предыдущий Snapshot для этого устройства
        previous_snapshot = self.event_repo.get_previous_snapshot(device_id, snapshot_id)

        # Запускаем все правила
        events = []
        for rule in self.rules:
            rule_events = rule.detect(previous_snapshot, current_snapshot)
            events.extend(rule_events)

        return events

    def process_and_save(self, current_snapshot: dict) -> List[Event]:
        """
        Анализирует Snapshot и сохраняет все события в БД.
        """
        events = self.analyze_snapshot(current_snapshot)
        if events:
            self.event_repo.save_events(events)
        return events
