#!/usr/bin/env python3
"""Rule Registry."""
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class RuleOperator(Enum):
    """Операторы для правил."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    ANY = "ANY"
    ALL = "ALL"

@dataclass
class RuleCondition:
    """Условие правила."""
    feature: str
    operator: str
    threshold: Any

@dataclass
class RuleDescriptor:
    """Дескриптор правила."""
    id: str
    engine: str
    name: str
    description: str
    category: str
    expression: List[RuleCondition]  # Переименовано с conditions
    logic: RuleOperator
    weight: int
    priority: int = 10
    enabled: bool = True
    version: str = "1.0.0"

class RuleRegistry:
    """Централизованный реестр правил."""
    
    _rules: Dict[str, RuleDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: RuleDescriptor):
        """Регистрирует правило."""
        cls._rules[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, rule_id: str) -> RuleDescriptor:
        """Получает дескриптор правила."""
        return cls._rules.get(rule_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, RuleDescriptor]:
        """Получает все правила."""
        return cls._rules.copy()
    
    @classmethod
    def get_by_engine(cls, engine: str) -> Dict[str, RuleDescriptor]:
        """Получает правила для конкретного движка."""
        return {k: v for k, v in cls._rules.items() if v.engine == engine}
    
    @classmethod
    def get_enabled(cls) -> List[RuleDescriptor]:
        """Получает все включённые правила."""
        return [r for r in cls._rules.values() if r.enabled]
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        """Проверяет зависимости правил."""
        errors = []
        
        from .feature_registry import FeatureRegistry
        
        for rule_id, descriptor in cls._rules.items():
            for condition in descriptor.expression:
                if condition.feature not in FeatureRegistry.get_all():
                    errors.append(f"Rule {rule_id} references unknown feature: {condition.feature}")
        
        return errors
