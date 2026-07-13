"""
Event Engine v1.4.0

Чистый вычислитель событий.
НЕ пишет в БД, НЕ отправляет уведомления.
Только отвечает на вопрос: "Что изменилось?"
"""

from .event import Event
from .event_type import EventType, Severity
from .result import EventResult
from .comparator import SnapshotComparator
from .engine import EventEngine

__all__ = [
    "Event",
    "EventType",
    "Severity",
    "EventResult",
    "SnapshotComparator",
    "EventEngine",
]
