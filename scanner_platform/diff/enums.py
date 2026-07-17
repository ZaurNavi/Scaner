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

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ChangeReason(Enum):
    ACTIVE_HTTP = "ACTIVE_HTTP"
    NEW_NETFLOW_DATA = "NEW_NETFLOW_DATA"
    NEW_SNMP_DATA = "NEW_SNMP_DATA"
    NEW_FACTS = "NEW_FACTS"
    DEVICE_REAPPEARED = "DEVICE_REAPPEARED"
    OUI_DATABASE_UPDATED = "OUI_DATABASE_UPDATED"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
