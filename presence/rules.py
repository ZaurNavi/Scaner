#!/usr/bin/env python3
"""Декларативные правила Presence Engine (без required_providers)."""
from dataclasses import dataclass
from typing import Any, Dict, Callable, List
import operator
from .categories import PresenceCategory
from .constants import *

@dataclass
class PresenceRule:
    id: str
    name: str
    category: PresenceCategory
    required_features: List[str]
    operator: str
    threshold: Any
    weight: int
    priority: int = 10
    enabled: bool = True

OPERATORS: Dict[str, Callable] = {
    "gt": operator.gt, "lt": operator.lt, "eq": operator.eq,
    "gte": operator.ge, "lte": operator.le,
}

def evaluate_condition(op: str, value: Any, threshold: Any) -> bool:
    if value is None: return False
    return OPERATORS.get(op, lambda x, y: False)(value, threshold)

PRESENCE_RULES = [
    PresenceRule(
        id="PRES-001", name="New Device", category=PresenceCategory.NEW_DEVICE,
        required_features=["history_depth_days"],
        operator="lt", threshold=NEW_DEVICE_HISTORY_DAYS, weight=60
    ),
    PresenceRule(
        id="PRES-002", name="Returning Device", category=PresenceCategory.RETURNING_DEVICE,
        required_features=["visit_count"],
        operator="gte", threshold=RETURNING_DEVICE_MIN_VISITS, weight=50
    ),
    PresenceRule(
        id="PRES-003", name="Regular Visitor", category=PresenceCategory.REGULAR_VISITOR,
        required_features=["visit_count"],
        operator="gte", threshold=REGULAR_VISITOR_MIN_VISITS, weight=45
    ),
    PresenceRule(
        id="PRES-004", name="Daily Visitor", category=PresenceCategory.DAILY_VISITOR,
        required_features=["active_days_ratio"],
        operator="gte", threshold=DAILY_VISITOR_MIN_DAYS / 30.0, weight=55
    ),
    PresenceRule(
        id="PRES-005", name="Weekend Visitor", category=PresenceCategory.WEEKEND_VISITOR,
        required_features=["weekend_activity_ratio"],
        operator="gte", threshold=WEEKEND_VISITOR_RATIO, weight=40
    ),
    PresenceRule(
        id="PRES-006", name="Night Visitor", category=PresenceCategory.NIGHT_VISITOR,
        required_features=["night_activity_ratio"],
        operator="gte", threshold=NIGHT_VISITOR_RATIO, weight=40
    ),
    PresenceRule(
        id="PRES-007", name="Business Hours Visitor", category=PresenceCategory.BUSINESS_HOURS_VISITOR,
        required_features=["business_hours_ratio"],
        operator="gte", threshold=BUSINESS_HOURS_RATIO, weight=45
    ),
]

def get_enabled_rules() -> List[PresenceRule]:
    return [r for r in PRESENCE_RULES if r.enabled]
