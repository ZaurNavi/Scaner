#!/usr/bin/env python3
"""
Timeline Factory — строит Presence Timeline из сырых данных (Замечание №2, №15).
Это часть Engine, не Provider.
"""
from datetime import datetime
from typing import List
from .models import PresenceTimeline, PresenceEvent
from .categories import EventType

class TimelineFactory:
    """Строит Timeline из сырых данных Providers."""
    
    def build(self, raw_data: dict) -> PresenceTimeline:
        events = []
        
        # First Seen
        first_seen = raw_data.get("first_seen")
        if first_seen:
            events.append(PresenceEvent(
                timestamp=datetime.fromisoformat(first_seen) if isinstance(first_seen, str) else first_seen,
                event_type=EventType.FIRST_SEEN,
                confidence=0.95
            ))
        
        # Last Seen
        last_seen = raw_data.get("last_seen")
        if last_seen:
            events.append(PresenceEvent(
                timestamp=datetime.fromisoformat(last_seen) if isinstance(last_seen, str) else last_seen,
                event_type=EventType.LAST_SEEN,
                confidence=0.95
            ))
        
        # Session Started (из snapshots)
        snapshots = raw_data.get("snapshots", [])
        for snap in snapshots:
            ts = snap.get("timestamp")
            if ts:
                events.append(PresenceEvent(
                    timestamp=datetime.fromisoformat(ts) if isinstance(ts, str) else ts,
                    event_type=EventType.SESSION_STARTED,
                    confidence=0.8,
                    details={"ip": snap.get("ip"), "hostname": snap.get("hostname")}
                ))
        
        # Сортируем по времени
        events.sort(key=lambda e: e.timestamp)
        
        return PresenceTimeline(events=events)
