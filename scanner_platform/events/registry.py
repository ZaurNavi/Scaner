#!/usr/bin/env python3
"""Event Rule Registry - thread-safe реестр правил генерации событий."""
from typing import List
from threading import Lock
from .rules.base_rule import BaseEventRule

class EventRuleRegistry:
    """Thread-safe Registry для Event Rules."""
    
    _rules: List[BaseEventRule] = []
    _lock = Lock()
    
    @classmethod
    def register(cls, rule: BaseEventRule):
        """Регистрирует правило (thread-safe)."""
        with cls._lock:
            # Защита от повторной регистрации
            if not any(isinstance(r, type(rule)) for r in cls._rules):
                cls._rules.append(rule)
    
    @classmethod
    def get_all(cls) -> List[BaseEventRule]:
        """Получает все зарегистрированные правила."""
        with cls._lock:
            return cls._rules.copy()
    
    @classmethod
    def clear(cls):
        """Очищает registry."""
        with cls._lock:
            cls._rules.clear()
