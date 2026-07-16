#!/usr/bin/env python3
"""Категории и статусы Usage Engine."""
from enum import Enum

class UsageCategory(Enum):
    HEAVY_USER = "heavy_user"
    LIGHT_USER = "light_user"
    BACKGROUND_DEVICE = "background_device"
    PERSISTENT_TRAFFIC = "persistent_traffic"
    UPLOAD_HEAVY = "upload_heavy"
    DOWNLOAD_HEAVY = "download_heavy"
    BURSTY_TRAFFIC = "bursty_traffic"
    BALANCED_TRAFFIC = "balanced_traffic"

class UsageStatus(Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CONFIRMED = "CONFIRMED"

class EventType(Enum):
    """Универсальные типы событий для Timeline."""
    TRAFFIC_SAMPLE = "traffic_sample"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    AP_CHANGED = "ap_changed"
    FIRST_SEEN = "first_seen"
    LAST_SEEN = "last_seen"
    AGGREGATED_SESSION = "aggregated_session"
    DAILY_WINDOW = "daily_window"
    HOURLY_WINDOW = "hourly_window"

class RuleOperator(Enum):
    """Операторы для правил."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    ANY = "ANY"
    ALL = "ALL"
