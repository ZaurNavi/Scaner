#!/usr/bin/env python3
"""
Декларативные правила поведения.
Использует класс Threshold и словарь операторов.
"""

from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional
import operator

from .categories import BehaviourCategory, BehaviourStatus
from .constants import *


@dataclass
class BehaviourThreshold:
    """Порог правила с поддержкой разных типов условий."""
    min: Optional[Any] = None
    max: Optional[Any] = None
    value: Optional[Any] = None  # Для eq, gt, lt


@dataclass
class BehaviourRule:
    """Декларативное правило поведения."""
    rule_id: str  # RULE-0001, RULE-0002, ...
    category: BehaviourCategory
    metric: str
    operator: str  # "gt", "lt", "eq", "between"
    threshold: BehaviourThreshold
    weight: int
    priority: int = 10
    enabled: bool = True
    description: str = ""


# Словарь операторов
OPERATORS: Dict[str, Callable] = {
    "gt": operator.gt,
    "lt": operator.lt,
    "eq": operator.eq,
    "gte": operator.ge,
    "lte": operator.le,
}


def evaluate_condition(rule_operator: str, value: Any, threshold: BehaviourThreshold) -> bool:
    """Вычисляет условие правила через словарь операторов."""
    if value is None:
        return False
    
    if rule_operator == "between":
        return threshold.min <= value <= threshold.max
    elif rule_operator in OPERATORS:
        return OPERATORS[rule_operator](value, threshold.value)
    
    return False


# Все правила вынесены сюда с уникальными ID
BEHAVIOUR_RULES = [
    # Мобильность
    BehaviourRule(
        rule_id="RULE-0001",
        category=BehaviourCategory.MOBILE,
        metric="ap_changes",
        operator="gt",
        threshold=BehaviourThreshold(value=MOBILE_AP_CHANGES_THRESHOLD),
        weight=40,
        priority=10,
        description=f"AP changes > {MOBILE_AP_CHANGES_THRESHOLD}"
    ),
    BehaviourRule(
        rule_id="RULE-0002",
        category=BehaviourCategory.ROAMING,
        metric="ap_changes",
        operator="gt",
        threshold=BehaviourThreshold(value=ROAMING_AP_CHANGES_THRESHOLD),
        weight=60,
        priority=10,
        description=f"AP changes > {ROAMING_AP_CHANGES_THRESHOLD}"
    ),
    BehaviourRule(
        rule_id="RULE-0003",
        category=BehaviourCategory.STATIONARY,
        metric="ap_changes",
        operator="lt",
        threshold=BehaviourThreshold(value=2),
        weight=30,
        priority=10,
        description="AP changes < 2"
    ),
    
    # Сессии
    BehaviourRule(
        rule_id="RULE-0004",
        category=BehaviourCategory.SHORT_SESSION,
        metric="average_session_duration",
        operator="lt",
        threshold=BehaviourThreshold(value=SHORT_SESSION_THRESHOLD),
        weight=30,
        priority=10,
        description=f"Average session < {SHORT_SESSION_THRESHOLD}s"
    ),
    BehaviourRule(
        rule_id="RULE-0005",
        category=BehaviourCategory.LONG_SESSION,
        metric="average_session_duration",
        operator="gt",
        threshold=BehaviourThreshold(value=LONG_SESSION_THRESHOLD),
        weight=40,
        priority=10,
        description=f"Average session > {LONG_SESSION_THRESHOLD}s"
    ),
    
    # Активность
    BehaviourRule(
        rule_id="RULE-0006",
        category=BehaviourCategory.IDLE,
        metric="idle_ratio",
        operator="gt",
        threshold=BehaviourThreshold(value=IDLE_RATIO_THRESHOLD),
        weight=35,
        priority=10,
        description=f"Idle ratio > {IDLE_RATIO_THRESHOLD*100}%"
    ),
    BehaviourRule(
        rule_id="RULE-0007",
        category=BehaviourCategory.ACTIVE,
        metric="active_ratio",
        operator="gt",
        threshold=BehaviourThreshold(value=ACTIVE_RATIO_THRESHOLD),
        weight=35,
        priority=10,
        description=f"Active ratio > {ACTIVE_RATIO_THRESHOLD*100}%"
    ),
    
    # Пользователи
    BehaviourRule(
        rule_id="RULE-0008",
        category=BehaviourCategory.LIGHT_USER,
        metric="total_traffic",
        operator="lt",
        threshold=BehaviourThreshold(value=LIGHT_USER_TRAFFIC_THRESHOLD),
        weight=25,
        priority=10,
        description=f"Total traffic < {LIGHT_USER_TRAFFIC_THRESHOLD // (1024*1024)} MB"
    ),
    BehaviourRule(
        rule_id="RULE-0009",
        category=BehaviourCategory.HEAVY_USER,
        metric="total_traffic",
        operator="gt",
        threshold=BehaviourThreshold(value=HEAVY_USER_TRAFFIC_THRESHOLD),
        weight=45,
        priority=10,
        description=f"Total traffic > {HEAVY_USER_TRAFFIC_THRESHOLD // (1024*1024)} MB"
    ),
    BehaviourRule(
        rule_id="RULE-0010",
        category=BehaviourCategory.NORMAL_USER,
        metric="total_traffic",
        operator="between",
        threshold=BehaviourThreshold(min=LIGHT_USER_TRAFFIC_THRESHOLD, max=HEAVY_USER_TRAFFIC_THRESHOLD),
        weight=20,
        priority=10,
        description=f"Total traffic between {LIGHT_USER_TRAFFIC_THRESHOLD // (1024*1024)}-{HEAVY_USER_TRAFFIC_THRESHOLD // (1024*1024)} MB"
    ),
]


def get_enabled_rules() -> list:
    """Возвращает все включённые правила."""
    return [rule for rule in BEHAVIOUR_RULES if rule.enabled]
