#!/usr/bin/env python3
"""Event Rule Registry - реестр правил генерации событий."""
from typing import List
from .rules.base_rule import BaseEventRule

class EventRuleRegistry:
    """Registry для Event Rules."""
    
    _rules: List[BaseEventRule] = []
    
    @classmethod
    def register(cls, rule: BaseEventRule):
        """Регистрирует правило."""
        cls._rules.append(rule)
    
    @classmethod
    def get_all(cls) -> List[BaseEventRule]:
        """Получает все зарегистрированные правила."""
        return cls._rules.copy()
    
    @classmethod
    def clear(cls):
        """Очищает registry."""
        cls._rules.clear()
