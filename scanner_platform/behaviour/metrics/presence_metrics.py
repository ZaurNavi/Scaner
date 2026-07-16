#!/usr/bin/env python3
"""Presence Metric Builders для Behaviour Engine."""
from datetime import datetime
from ...timeline.models import Timeline, EventType

def build_daily_presence(timeline: Timeline) -> float:
    """Доля дней с активностью за период наблюдения."""
    events = timeline.events
    if not events:
        return 0.0
    
    start, end = timeline.get_time_range()
    if not start or not end:
        return 0.0
    
    total_days = max((end - start).days, 1)
    active_days = len(set(e.timestamp.date() for e in events))
    
    return min(active_days / total_days, 1.0)

def build_weekly_presence(timeline: Timeline) -> float:
    """Доля недель с активностью."""
    events = timeline.events
    if not events:
        return 0.0
    
    start, end = timeline.get_time_range()
    if not start or not end:
        return 0.0
    
    total_weeks = max((end - start).days // 7, 1)
    active_weeks = len(set(e.timestamp.isocalendar()[1] for e in events))
    
    return min(active_weeks / total_weeks, 1.0)

def build_weekend_presence(timeline: Timeline) -> float:
    """Доля активности в выходные (суббота=5, воскресенье=6)."""
    events = timeline.events
    if not events:
        return 0.0
    
    weekend_events = [e for e in events if e.timestamp.weekday() >= 5]
    return len(weekend_events) / len(events)

def build_weekday_ratio(timeline: Timeline) -> float:
    """Доля активности в будни."""
    events = timeline.events
    if not events:
        return 0.0
    
    weekday_events = [e for e in events if e.timestamp.weekday() < 5]
    return len(weekday_events) / len(events)
