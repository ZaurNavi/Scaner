#!/usr/bin/env python3
import operator
from typing import Dict, Any

OPERATORS = {
    "gt": operator.gt, "lt": operator.lt, "eq": operator.eq,
    "gte": operator.ge, "lte": operator.le, "ne": operator.ne,
}

class RuleEvaluator:
    """Оценивает правила на основе Features."""
    def evaluate(self, rule, features: Dict[str, Any]) -> bool:
        for condition in rule.expression:
            feature_value = features.get(condition.feature)
            if feature_value is None:
                return False
            op_func = OPERATORS.get(condition.operator)
            if not op_func or not op_func(feature_value, condition.threshold):
                return False
        return True
