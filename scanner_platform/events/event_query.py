#!/usr/bin/env python3
"""Event Query API - immutable builder pattern с оптимизацией."""
from typing import List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EventQuery:
    """
    Immutable Query API для DomainEventSet (builder pattern).
    
    ОПТИМИЗАЦИЯ: фильтры накапливаются, применяются только при _execute().
    Это избегает создания промежуточных tuple при chaining.
    """
    _events: Tuple[Any, ...] = field(default_factory=tuple)
    _device_uuid: Optional[str] = None
    _event_type: Optional[str] = None
    _engine: Optional[str] = None
    _category: Optional[str] = None
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
            _engine=self._engine,
            _category=self._category,
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
            _engine=self._engine,
            _category=self._category,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=self._change_id
        )
    
    def by_engine(self, engine: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по engine (из payload)."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=self._event_type,
            _engine=engine,
            _category=self._category,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=self._change_id
        )
    
    def by_category(self, category: str) -> 'EventQuery':
        """Возвращает новый EventQuery с фильтром по category (из payload)."""
        return EventQuery(
            _events=self._events,
            _device_uuid=self._device_uuid,
            _event_type=self._event_type,
            _engine=self._engine,
            _category=category,
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
            _engine=self._engine,
            _category=self._category,
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
            _engine=self._engine,
            _category=self._category,
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
            _engine=self._engine,
            _category=self._category,
            _time_from=self._time_from,
            _time_to=self._time_to,
            _diff_id=self._diff_id,
            _change_id=change_id
        )
    
    def _matches(self, event: Any) -> bool:
        """
        Проверяет, соответствует ли событие всем фильтрам.
        ОПТИМИЗАЦИЯ: один проход по событию, без создания промежуточных tuple.
        """
        if self._device_uuid and event.device_uuid != self._device_uuid:
            return False
        
        if self._event_type and event.event_type != self._event_type:
            return False
        
        if self._time_from and event.occurred_at < self._time_from:
            return False
        
        if self._time_to and event.occurred_at > self._time_to:
            return False
        
        if self._diff_id and event.source_diff_id != self._diff_id:
            return False
        
        if self._change_id and event.source_change_id != self._change_id:
            return False
        
        # Фильтры по payload (engine и category)
        if self._engine or self._category:
            payload = event.payload
            if self._engine and payload.get("engine") != self._engine:
                return False
            if self._category and payload.get("category") != self._category:
                return False
        
        return True
    
    def _execute(self) -> List[Any]:
        """
        Выполняет фильтрацию за ОДИН проход.
        ОПТИМИЗАЦИЯ: нет промежуточных tuple, только один list.
        """
        return [e for e in self._events if self._matches(e)]
    
    def all(self) -> List[Any]:
        """Возвращает все отфильтрованные события."""
        return self._execute()
    
    def first(self) -> Optional[Any]:
        """Возвращает первое событие (лениво — останавливается после первого совпадения)."""
        for e in self._events:
            if self._matches(e):
                return e
        return None
    
    def last(self) -> Optional[Any]:
        """Возвращает последнее событие."""
        result = None
        for e in self._events:
            if self._matches(e):
                result = e
        return result
    
    def count(self) -> int:
        """Возвращает количество событий (без создания list)."""
        return sum(1 for e in self._events if self._matches(e))
