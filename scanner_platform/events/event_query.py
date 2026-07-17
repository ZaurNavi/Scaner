#!/usr/bin/env python3
"""Event Query API для фильтрации событий."""
from typing import List, Optional, Any
from datetime import datetime

class EventQuery:
    """Fluent Query API для DomainEventSet."""
    
    def __init__(self, events: List[Any]):
        self._events = events
        self._device_uuid: Optional[str] = None
        self._event_type: Optional[str] = None
        self._time_from: Optional[datetime] = None
        self._time_to: Optional[datetime] = None
        self._engine: Optional[str] = None
        self._category: Optional[str] = None
        self._diff_id: Optional[str] = None
        self._change_id: Optional[str] = None
    
    def by_device(self, device_uuid: str) -> 'EventQuery':
        self._device_uuid = device_uuid
        return self
    
    def by_type(self, event_type: str) -> 'EventQuery':
        self._event_type = event_type
        return self
    
    def by_time(self, time_from: datetime, time_to: datetime = None) -> 'EventQuery':
        self._time_from = time_from
        self._time_to = time_to
        return self
    
    def by_engine(self, engine: str) -> 'EventQuery':
        self._engine = engine
        return self
    
    def by_category(self, category: str) -> 'EventQuery':
        self._category = category
        return self
    
    def by_diff(self, diff_id: str) -> 'EventQuery':
        self._diff_id = diff_id
        return self
    
    def by_change(self, change_id: str) -> 'EventQuery':
        self._change_id = change_id
        return self
    
    def _execute(self) -> List[Any]:
        results = self._events
        
        if self._device_uuid:
            results = [e for e in results if e.device_uuid == self._device_uuid]
        
        if self._event_type:
            results = [e for e in results if e.event_type == self._event_type]
        
        if self._time_from:
            results = [e for e in results if e.occurred_at >= self._time_from]
        
        if self._time_to:
            results = [e for e in results if e.occurred_at <= self._time_to]
        
        if self._diff_id:
            results = [e for e in results if e.source_diff_id == self._diff_id]
        
        if self._change_id:
            results = [e for e in results if e.source_change_id == self._change_id]
        
        return results
    
    def all(self) -> List[Any]:
        return self._execute()
    
    def first(self) -> Optional[Any]:
        results = self._execute()
        return results[0] if results else None
    
    def last(self) -> Optional[Any]:
        results = self._execute()
        return results[-1] if results else None
    
    def count(self) -> int:
        return len(self._execute())
