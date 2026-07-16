#!/usr/bin/env python3
"""Rule Registry."""
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class RuleOperator(Enum):
    AND = "AND"; OR = "OR"; NOT = "NOT"; ANY = "ANY"; ALL = "ALL"

@dataclass
class RuleCondition:
    feature: str
    operator: str
    threshold: Any

@dataclass
class RuleDescriptor:
    id: str
    engine: str
    name: str
    description: str
    category: str
    expression: List[RuleCondition]
    logic: RuleOperator
    weight: int
    priority: int = 10
    enabled: bool = True
    version: str = "1.0.0"

class RuleRegistry:
    _rules: Dict[str, RuleDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: RuleDescriptor):
        cls._rules[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, rule_id: str) -> RuleDescriptor:
        return cls._rules.get(rule_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, RuleDescriptor]:
        return cls._rules.copy()
    
    @classmethod
    def get_by_engine(cls, engine: str) -> Dict[str, RuleDescriptor]:
        return {k: v for k, v in cls._rules.items() if v.engine == engine}
    
    @classmethod
    def get_enabled(cls) -> List[RuleDescriptor]:
        return [r for r in cls._rules.values() if r.enabled]
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        errors = []
        for rule_id, descriptor in cls._rules.items():
            for condition in descriptor.expression:
                if condition.feature not in FeatureRegistry.get_all():
                    errors.append(f"Rule {rule_id} references unknown feature: {condition.feature}")
        return errors

# Импортируем в конце
from .feature_registry import FeatureRegistry
