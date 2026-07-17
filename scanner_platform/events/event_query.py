#!/usr/bin/env python3
"""Event Query API - immutable builder pattern."""
from typing import List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EventQuery:
    """Immutable Query API для DomainEventSet (builder pattern)."""
    _events: Tuple[Any, ...] = field(default_factory=tuple)
    _device_uuid: Optional[str] = None
    _event_type: Optional[str] = None
    _time_from: Optional[datetime] = None
    _time_to: Optional[datetime] = None
    _diff_id: Optional[str] = None
    _change_id: Optional[str] = None
    
    def by_device(self, device_uuid: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по device."""
        return EventQuery(
            _events=self._events,
            _device_uuid=device_uuid,
            _event_type=self._event_type,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=self._change_id
        )
    
    def by_type(self, event_type: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по типу."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=event_type,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=self._change_id
        )
    
    def by_time(self, time_from: datetime, time_to: datetime = None) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по времени."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=self._event_type,
            _time_from=time_from,
            _time_to=time_to,
            _diff_id=self._diff_id,
            _change_id=self._change_id
        )
    
    def by_diff(self, diff_id: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по diff_id."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=self._event_type,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=diff_id,
            _change_id=self._change_id
        )
    
    def by_change(self, change_id: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по change_id."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=self._event_type,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=change_id
        )
    
    def _execute(self) -> List[Any]:
        """Выполняет фильтрацию (без лишних копий)."""
        results = self._events  # Работаем с tuple напрямую
        
        if self._device_uuid:
            results = tuple(e for e in results if e.device_uuid == self._device_uuid)
        
        if self._event_type:
            results = tuple(e for e in results if e.event_type == self._event_type)
        
        if self._time_from:
            results = tuple(e for e in results if e.occurred_at >= self._time_from)
        
        if self._time_to:
            results = tuple(e for e in results if e.occurred_at <= self._time_to)
        
        if self._diff_id:
            results = tuple(e for e in results if e.source_diff_id == self._diff_id)
        
        if self._change_id:
            results = tuple(e for e in results if e.source_change_id == self._change_id)
        
        return list(results)  # Возвращаем list только в конце
    
    def all(self) -> List[Any]:
        """Возвращает все отфильтрованные события."""
        return self._execute()
    
    def first(self) -> Optional[Any]:
        """Возвращает первое событие."""
        results = self._execute()
        return results[0] if results else None
    
    def last(self) -> Optional[Any]:
        """Возвращает последнее событие."""
        results = self._execute()
        return results[-1] if results else None
    
    def count(self) -> int:
        """Возвращает количество событий."""
        return len(self._execute())
