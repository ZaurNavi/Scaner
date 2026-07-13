from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .event import Event


@dataclass(frozen=True)
class EventResult:
    """
    Результат работы Event Engine.
    Содержит список событий и метаданные о вычислении.
    """
    events: List[Event] = field(default_factory=list)
    elapsed_ms: float = 0.0

    @property
    def count(self) -> int:
        return len(self.events)

    def filter_by_severity(self, severity) -> List[Event]:
        return [e for e in self.events if e.severity == severity]
