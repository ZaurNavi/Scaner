#!/usr/bin/env python3
"""Activity Metric Builders для Behaviour Engine."""
from datetime import datetime
from ...timeline.models import Timeline, EventType

def build_active_hours(timeline: Timeline) -> float:
    """Общее количество часов активности."""
    events = timeline.events
    if not events:
        return 0.0
    
    start, end = timeline.get_time_range()
    if not start or not end:
        return 0.0
    
    return (end - start).total_seconds() / 3600

def build_night_activity(timeline: Timeline) -> float:
    """Доля активности в ночное время (22:00 - 06:00)."""
    events = timeline.events
    if not events:
        return 0.0
    
    night_events = [e for e in events if e.timestamp.hour >= 22 or e.timestamp.hour < 6]
    return len(night_events) / len(events)

def build_office_hours_activity(timeline: Timeline) -> float:
    """Доля активности в рабочие часы (09:00 - 18:00)."""
    events = timeline.events
    if not events:
        return 0.0
    
    office_events = [e for e in events if 9 <= e.timestamp.hour < 18]
    return len(office_events) / len(events)
