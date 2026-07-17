#!/usr/bin/env python3
"""Перечисления для Change Detection Layer."""
from enum import Enum

class ChangeType(Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    UPDATED = "UPDATED"
    MOVED = "MOVED"
    RECOVERED = "RECOVERED"
    STATE_CHANGED = "STATE_CHANGED"

class CapabilityState(Enum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PARTIAL = "PARTIAL"
    AVAILABLE = "AVAILABLE"
