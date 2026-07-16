#!/usr/bin/env python3
"""Session Metric Builders для Behaviour Engine."""
from datetime import datetime
from typing import Dict  # <-- ДОБАВЛЕНО
from ...timeline.models import Timeline, EventType

def build_appearance_frequency(timeline: Timeline) -> int:
    """Количество появлений устройства."""
    events = timeline.get_by_type(EventType.SESSION_STARTED)
    return len(events)

def build_online_duration(timeline: Timeline) -> float:
    """Общая продолжительность онлайн (в секундах)."""
    events = timeline.events
    if not events:
        return 0.0
    
    start, end = timeline.get_time_range()
    if not start or not end:
        return 0.0
    
    return (end - start).total_seconds()

def build_idle_duration(timeline: Timeline) -> float:
    """Доля времени без активности (упрощённо: 1 - active_ratio)."""
    events = timeline.events
    if not events:
        return 0.0
    
    start, end = timeline.get_time_range()
    if not start or not end:
        return 0.0
    
    total_seconds = (end - start).total_seconds()
    # Упрощённо: считаем время между событиями как "активное"
    active_seconds = len(events) * 60  # 1 минута на событие
    idle_seconds = max(total_seconds - active_seconds, 0)
    
    return idle_seconds / total_seconds if total_seconds > 0 else 0.0

def build_session_distribution(timeline: Timeline) -> Dict[str, int]:
    """Распределение сессий по времени суток."""
    events = timeline.get_by_type(EventType.SESSION_STARTED)
    
    distribution = {
        "morning": 0,   # 06-12
        "afternoon": 0, # 12-18
        "evening": 0,   # 18-22
        "night": 0      # 22-06
    }
    
    for event in events:
        hour = event.timestamp.hour
        if 6 <= hour < 12:
            distribution["morning"] += 1
        elif 12 <= hour < 18:
            distribution["afternoon"] += 1
        elif 18 <= hour < 22:
            distribution["evening"] += 1
        else:
            distribution["night"] += 1
    
    return distribution
