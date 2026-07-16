#!/usr/bin/env python3
"""Декларативные правила Mobility Engine."""
from dataclasses import dataclass
from typing import Any, Dict, Callable, List
import operator

from .categories import MobilityCategory
from .constants import *

@dataclass
class MobilityRule:
    id: str
    name: str
    category: MobilityCategory
    required_features: List[str]
    operator: str
    threshold: Any
    weight: int
    priority: int = 10
    enabled: bool = True

OPERATORS: Dict[str, Callable] = {
    "gt": operator.gt,
    "lt": operator.lt,
    "eq": operator.eq,
    "gte": operator.ge,
    "lte": operator.le,
}

def evaluate_condition(op: str, value: Any, threshold: Any) -> bool:
    if value is None: return False
    if op in OPERATORS:
        return OPERATORS[op](value, threshold)
    return False

MOBILITY_RULES = [
    MobilityRule(
        id="MOB-001", name="High Roaming", category=MobilityCategory.ROAMER,
        required_features=["roaming_rate"], operator="gt", threshold=ROAMING_RATE_THRESHOLD, weight=50
    ),
    MobilityRule(
        id="MOB-002", name="Stationary Device", category=MobilityCategory.STATIONARY,
        required_features=["stationary_ratio"], operator="gte", threshold=STATIONARY_RATIO_THRESHOLD, weight=40
    ),
    MobilityRule(
        id="MOB-003", name="Nomadic User", category=MobilityCategory.NOMADIC,
        required_features=["unique_ap_count"], operator="gte", threshold=MOVEMENT_RADIUS_THRESHOLD, weight=30
    ),
]

def get_enabled_rules() -> List[MobilityRule]:
    return [r for r in MOBILITY_RULES if r.enabled]
