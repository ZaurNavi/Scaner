#!/usr/bin/env python3
"""Platform Timeline Models."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class EventType(Enum):
    """Универсальные типы событий для всей платформы."""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AP_CHANGED = "ap_changed"
    SSID_CHANGED = "ssid_changed"
    IP_CHANGED = "ip_changed"
    LEASE_RENEWED = "lease_renewed"
    
    # Traffic events
    TRAFFIC_SAMPLE = "traffic_sample"
    TRAFFIC_SPIKE = "traffic_spike"
    
    # Signal events
    RSSI_CHANGED = "rssi_changed"
    SIGNAL_CHANGED = "signal_changed"
    
    # State events
    STATE_CHANGED = "state_changed"
    AUTHENTICATED = "authenticated"
    DEAUTHENTICATED = "deauthenticated"
    
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    
    # Identity events
    FIRST_SEEN = "first_seen"
    LAST_SEEN = "last_seen"
    
    # Aggregation events
    AGGREGATED_SESSION = "aggregated_session"
    DAILY_WINDOW = "daily_window"
    HOURLY_WINDOW = "hourly_window"

@dataclass
class TimelineEvent:
    """Единый объект события для всей платформы."""
    id: str
    timestamp: datetime
    device_id: str
    event_type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    quality: float = 0.9
    confidence: float = 90.0
    version: str = "1.0.0"

@dataclass
class Timeline:
    """Центральный объект Timeline для всей платформы (read-only)."""
    events: List[TimelineEvent] = field(default_factory=list)
    device_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    
    def is_immutable(self) -> bool:
        return True
    
    def get_by_type(self, event_type: EventType) -> List[TimelineEvent]:
        """Возвращает события указанного типа."""
        return [e for e in self.events if e.event_type == event_type]
    
    def count_by_type(self, event_type: EventType) -> int:
        """Подсчитывает количество событий указанного типа."""
        return len(self.get_by_type(event_type))
    
    def get_by_source(self, source: str) -> List[TimelineEvent]:
        """Возвращает события от указанного источника."""
        return [e for e in self.events if e.source == source]
    
    def get_time_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Возвращает временной диапазон событий (min, max).
        
        Returns:
            Tuple[Optional[datetime], Optional[datetime]]: (start_time, end_time)
            Если событий нет, возвращает (None, None)
        """
        if not self.events:
            return (None, None)
        
        timestamps = [e.timestamp for e in self.events]
        return (min(timestamps), max(timestamps))
