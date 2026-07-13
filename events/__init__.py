"""
Event Engine v1.4.0 + Persistence Layer v1.4.1

Event Engine — чистый вычислитель событий.
Event Persister — слой сохранения событий.
"""

from .event import Event
from .event_type import EventType, Severity
from .result import EventResult
from .comparator import SnapshotComparator
from .engine import EventEngine
from .repository import EventRepository
from .persister import EventPersister, PersistResult

__all__ = [
    "Event",
    "EventType",
    "Severity",
    "EventResult",
    "SnapshotComparator",
    "EventEngine",
    "EventRepository",
    "EventPersister",
    "PersistResult",
]
