#!/usr/bin/env python3
"""Severity Resolver — определяет важность изменений."""
from .enums import ChangeType, Severity

class SeverityResolver:
    """
    Определяет Severity на основе типа изменения и категории.
    Позволяет менять политику важности без изменения ядра Diff Engine.
    """
    
    @staticmethod
    def resolve(change_type: ChangeType, category: str) -> Severity:
        # Пример базовой политики
        if change_type == ChangeType.REMOVED:
            return Severity.HIGH
        if change_type == ChangeType.ADDED and category == "risk":
            return Severity.CRITICAL
        if change_type == ChangeType.UPDATED:
            return Severity.MEDIUM
        if change_type == ChangeType.STATE_CHANGED:
            return Severity.HIGH
        
        return Severity.LOW
