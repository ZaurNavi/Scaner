#!/usr/bin/env python3
"""
Rule & Attribute Registry.
ES-1.8.3: Введен AttributeRegistry. Rule выбирается ТОЛЬКО по attribute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Type

from .models import NormalizationResult, Observation, ObservationCategory


# ==============================================================================
# Attribute Registry (ES-1.8.3)
# ==============================================================================

@dataclass(frozen=True)
class AttributeDescriptor:
    id: str
    category: ObservationCategory
    value_type: Type
    description: str

class AttributeRegistry:
    _attributes: Dict[str, AttributeDescriptor] = {}

    @classmethod
    def register(cls, desc: AttributeDescriptor):
        if desc.id in cls._attributes:
            raise ValueError(f"Attribute '{desc.id}' already registered")
        cls._attributes[desc.id] = desc

    @classmethod
    def get(cls, attr_id: str) -> Optional[AttributeDescriptor]:
        return cls._attributes.get(attr_id)

    @classmethod
    def validate(cls, attribute: str, value: Any) -> bool:
        desc = cls.get(attribute)
        if not desc:
            return False
        # Простая проверка типа (можно расширить)
        if not isinstance(value, desc.value_type):
            # Допускаем None или пустые значения для опциональных полей
            if value is not None and not (isinstance(value, list) and len(value) == 0):
                return False
        return True


# ==============================================================================
# Rule Registry (ES-1.8.3: Выбор ТОЛЬКО по attribute)
# ==============================================================================

@dataclass(frozen=True)
class RuleDescriptor:
    id: str
    category: ObservationCategory
    attribute: str
    protocol: str  # Только для информации, НЕ используется для выбора!
    priority: int
    description: str
    handler: Callable[[Observation], NormalizationResult]
    version: str = "1.0.0"

    def apply(self, observation: Observation) -> NormalizationResult:
        return self.handler(observation)


class RuleRegistry:
    _descriptors: Dict[str, RuleDescriptor] = {}
    _rules_by_attribute: Dict[str, List[RuleDescriptor]] = {}

    @classmethod
    def register(cls, descriptor: RuleDescriptor):
        if descriptor.id in cls._descriptors:
            raise ValueError(f"Rule ID '{descriptor.id}' already registered")
        cls._descriptors[descriptor.id] = descriptor
        
        if descriptor.attribute not in cls._rules_by_attribute:
            cls._rules_by_attribute[descriptor.attribute] = []
        cls._rules_by_attribute[descriptor.attribute].append(descriptor)
        cls._rules_by_attribute[descriptor.attribute].sort(key=lambda d: d.priority)

    @classmethod
    def get_rule(cls, attribute: str) -> Optional[RuleDescriptor]:
        """ES-1.8.3: Выбирает правило ТОЛЬКО по attribute. Protocol игнорируется при выборе."""
        rules = cls._rules_by_attribute.get(attribute, [])
        return rules[0] if rules else None

    @classmethod
    def get_all_rules(cls) -> List[RuleDescriptor]:
        return list(cls._descriptors.values())

    @classmethod
    def count(cls) -> int:
        return len(cls._descriptors)

    @classmethod
    def clear(cls) -> None:
        cls._descriptors.clear()
        cls._rules_by_attribute.clear()


def normalization_rule(
    id: str,
    category: ObservationCategory,
    attribute: str,
    protocol: str,
    priority: int = 100,
    description: str = "",
    version: str = "1.0.0"
):
    def decorator(func: Callable[[Observation], NormalizationResult]):
        descriptor = RuleDescriptor(
            id=id, category=category, attribute=attribute, protocol=protocol,
            priority=priority, description=description, handler=func, version=version
        )
        RuleRegistry.register(descriptor)
        return func
    return decorator
