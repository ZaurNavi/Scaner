#!/usr/bin/env python3
"""Категории, статусы и типы событий Presence Engine."""
from enum import Enum

class PresenceCategory(Enum):
    NEW_DEVICE = "new_device"
    RETURNING_DEVICE = "returning_device"
    REGULAR_VISITOR = "regular_visitor"
    RARE_VISITOR = "rare_visitor"
    DAILY_VISITOR = "daily_visitor"
    WEEKEND_VISITOR = "weekend_visitor"
    NIGHT_VISITOR = "night_visitor"
    BUSINESS_HOURS_VISITOR = "business_hours_visitor"

class PresenceStatus(Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CONFIRMED = "CONFIRMED"

# EventType enum (Замечание №8: убраны APPEARED/DISAPPEARED)
class EventType(Enum):
    FIRST_SEEN = "first_seen"
    LAST_SEEN = "last_seen"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    RETURNED = "returned"
    LONG_ABSENCE = "long_absence"
