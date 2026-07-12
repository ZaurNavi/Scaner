"""
Correlation Engine — объединяет данные из всех источников.
"""

from .engine import CorrelationEngine, engine
from .evidence import Evidence
from .result import CorrelationResult, ConfidenceBreakdown, MatchedRule
from .rules import ALL_RULES
from .rules.base import Rule

__all__ = [
    "CorrelationEngine",
    "engine",
    "Evidence",
    "CorrelationResult",
    "ConfidenceBreakdown",
    "MatchedRule",
    "ALL_RULES",
    "Rule",
]
