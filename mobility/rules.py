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
    required_providers: List[str] # <-- ДОБАВЛЕНО
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

MOBILITY_RULES = [
    MobilityRule(
        id="MOB-001", name="High Roaming", category=MobilityCategory.ROAMER,
        required_features=["roaming_rate"], required_providers=["session_provider"],
        operator="gt", threshold=ROAMING_RATE_THRESHOLD, weight=50
    ),
    MobilityRule(
        id="MOB-002", name="Stationary Device", category=MobilityCategory.STATIONARY,
        required_features=["stationary_ratio"], required_providers=["behaviour_provider"],
        operator="gte", threshold=STATIONARY_RATIO_THRESHOLD, weight=40
    ),
]

def get_enabled_rules() -> List[MobilityRule]:
    return [r for r in MOBILITY_RULES if r.enabled]
