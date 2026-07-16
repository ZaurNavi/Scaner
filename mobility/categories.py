#!/usr/bin/env python3
"""Категории и статусы Mobility Engine."""
from enum import Enum

class MobilityCategory(Enum):
    STATIONARY = "stationary"
    NOMADIC = "nomadic"
    ROAMER = "roamer"
    HIGHLY_MOBILE = "highly_mobile"
    PREDICTABLE_PATTERN = "predictable_pattern"
    ERRATIC_MOVEMENT = "erratic_movement"

class MobilityStatus(Enum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CONFIRMED = "CONFIRMED"
