#!/usr/bin/env python3
"""Константы для Domain Event Layer."""

# Subject типы
class SubjectType:
    FACT = "fact"
    SUMMARY = "summary"
    CAPABILITY = "capability"
    ENGINE = "engine"

# Category типы
class CategoryType:
    PRESENCE = "presence"
    USAGE = "usage"
    BEHAVIOUR = "behaviour"
    MOBILITY = "mobility"
    SESSIONS = "sessions"
    FACTS = "facts"
    CONFIDENCE = "confidence"
    HISTORY_DEPTH = "history_depth"
    LAST_SEEN = "last_seen"
