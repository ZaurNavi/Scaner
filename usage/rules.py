#!/usr/bin/env python3
"""Декларативные правила Usage Engine (работают по Features, поддерживают AND/OR/NOT/ANY/ALL)."""
from dataclasses import dataclass
from typing import Any, Dict, Callable, List, Union
import operator
from .categories import UsageCategory, RuleOperator

@dataclass
class RuleCondition:
    """Условие правила (работает по Feature, не по Metric!)."""
    feature: str
    operator: str
    threshold: Any

@dataclass
class UsageRule:
    id: str
    name: str
    description: str
    category: UsageCategory
    conditions: List[RuleCondition]
    logic: RuleOperator = RuleOperator.AND  # AND, OR, NOT, ANY, ALL
    weight: int
    priority: int = 10
    enabled: bool = True
    version: str = "1.0.0"

OPERATORS: Dict[str, Callable] = {
    "gt": operator.gt, "lt": operator.lt, "eq": operator.eq,
    "gte": operator.ge, "lte": operator.le, "ne": operator.ne,
}

def evaluate_condition(op: str, value: Any, threshold: Any) -> bool:
    if value is None: return False
    return OPERATORS.get(op, lambda x, y: False)(value, threshold)

USAGE_RULES = [
    UsageRule(
        id="USAGE-001", name="Heavy User", description="Устройство потребляет более 500 МБ",
        category=UsageCategory.HEAVY_USER,
        conditions=[RuleCondition("usage_class", "eq", "heavy")],
        logic=RuleOperator.AND,
        weight=50
    ),
    UsageRule(
        id="USAGE-002", name="Light User", description="Устройство потребляет менее 10 МБ",
        category=UsageCategory.LIGHT_USER,
        conditions=[RuleCondition("usage_class", "eq", "light")],
        logic=RuleOperator.AND,
        weight=40
    ),
    UsageRule(
        id="USAGE-003", name="Background Device", description="Низкая активность, фоновый трафик",
        category=UsageCategory.BACKGROUND_DEVICE,
        conditions=[RuleCondition("usage_class", "eq", "background")],
        logic=RuleOperator.AND,
        weight=45
    ),
    UsageRule(
        id="USAGE-004", name="Persistent Traffic", description="Постоянный трафик в течение дня",
        category=UsageCategory.PERSISTENT_TRAFFIC,
        conditions=[RuleCondition("usage_class", "eq", "persistent")],
        logic=RuleOperator.AND,
        weight=50
    ),
    UsageRule(
        id="USAGE-005", name="Upload Heavy", description="Преобладает исходящий трафик",
        category=UsageCategory.UPLOAD_HEAVY,
        conditions=[RuleCondition("upload_dominant", "eq", True)],
        logic=RuleOperator.AND,
        weight=45
    ),
    UsageRule(
        id="USAGE-006", name="Download Heavy", description="Преобладает входящий трафик",
        category=UsageCategory.DOWNLOAD_HEAVY,
        conditions=[RuleCondition("download_dominant", "eq", True)],
        logic=RuleOperator.AND,
        weight=45
    ),
    UsageRule(
        id="USAGE-007", name="Bursty Traffic", description="Трафик bursts",
        category=UsageCategory.BURSTY_TRAFFIC,
        conditions=[RuleCondition("bursty_traffic", "eq", True)],
        logic=RuleOperator.AND,
        weight=40
    ),
    UsageRule(
        id="USAGE-008", name="Balanced Traffic", description="Сбалансированный трафик",
        category=UsageCategory.BALANCED_TRAFFIC,
        conditions=[
            RuleCondition("upload_dominant", "eq", False),
            RuleCondition("download_dominant", "eq", False)
        ],
        logic=RuleOperator.AND,
        weight=35
    ),
]

def get_enabled_rules() -> List[UsageRule]:
    return [r for r in USAGE_RULES if r.enabled]
