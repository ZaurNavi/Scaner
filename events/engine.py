from __future__ import annotations
import time
from typing import Optional

from .comparator import SnapshotComparator
from .result import EventResult
from .event import Event


class EventEngine:
    """
    Event Engine — чистый вычислитель событий.
    
    НЕ хранит историю.
    НЕ пишет в базу.
    НЕ отправляет уведомления.
    
    Только вычисляет: "Что изменилось между предыдущим и текущим состоянием?"
    """

    def __init__(self, repository):
        """
        repository: объект с методом get_last_snapshot(device_id) -> dict | None
        """
        self.repository = repository
        self.comparator = SnapshotComparator()

    def analyze(self, device_id: str, new_snapshot: dict) -> EventResult:
        """
        Вычисляет события для устройства.
        
        1. Запрашивает предыдущий Snapshot через Repository
        2. Запускает Comparator
        3. Возвращает EventResult
        """
        start_time = time.time()

        # Получаем предыдущий Snapshot
        old_snapshot = self.repository.get_last_snapshot(device_id)

        # Запускаем Comparator
        events = self.comparator.compare(old_snapshot, new_snapshot)

        elapsed_ms = (time.time() - start_time) * 1000

        return EventResult(events=events, elapsed_ms=elapsed_ms)
