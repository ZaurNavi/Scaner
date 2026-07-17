#!/usr/bin/env python3
"""DomainEventSet - immutable коллекция событий."""
from dataclasses import dataclass, field
from typing import Tuple, Optional, Any, Dict
from datetime import datetime
from .base import DomainEvent
from .event_query import EventQuery
from .serializer import EventSerializer

@dataclass(frozen=True)
class DomainEventSet:
    """Immutable коллекция доменных событий."""
    events: Tuple[DomainEvent, ...] = field(default_factory=tuple)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def query(self) -> EventQuery:
        """Возвращает Query API."""
        return EventQuery(list(self.events))
    
    def serialize(self, format: str = "json") -> str:
        """Сериализует события."""
        return EventSerializer.serialize(self, format)
    
    def count(self) -> int:
        return len(self.events)
    
    def first(self) -> Optional[DomainEvent]:
        return self.events[0] if self.events else None
    
    def last(self) -> Optional[DomainEvent]:
        return self.events[-1] if self.events else None
    
    def __len__(self) -> int:
        return len(self.events)
    
    def __iter__(self):
        return iter(self.events)

# Глобальный пустой EventSet для идемпотентности
EMPTY_EVENT_SET = DomainEventSet(events=tuple(), generated_at=datetime.min)
