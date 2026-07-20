#!/usr/bin/env python3
"""
Rule Registry — реестр дескрипторов правил нормализации.
ES-1.8.1: RuleDescriptor (симметрия с Active Registry).

Архитектура:
- Registry хранит только RuleDescriptor
- Каждое правило определяет категорию (Normalizer не угадывает)
- Автоматическая регистрация через декоратор
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .models import NormalizationResult, Observation, ObservationCategory


# ==============================================================================
# RuleDescriptor — полное описание правила (пункт 6)
# ==============================================================================

@dataclass(frozen=True)
class RuleDescriptor:
    """
    Полное описание правила нормализации.
    
    ES-1.8.1 (пункт 6): Симметрия с PassiveCollectorDescriptor.
    Registry хранит только Descriptor.
    """
    id: str
    category: ObservationCategory
    attribute: str
    protocol: str  # Какой протокол обрабатывает (DNS, mDNS, LLMNR и т.д.)
    priority: int
    description: str
    handler: Callable[[Observation], NormalizationResult]
    version: str = "1.0.0"
    
    def apply(self, observation: Observation) -> NormalizationResult:
        """Применяет правило к Observation."""
        return self.handler(observation)


# ==============================================================================
# RuleRegistry — реестр правил
# ==============================================================================

class RuleRegistry:
    """
    Реестр правил нормализации.
    
    ES-1.8.1:
    - Хранит только RuleDescriptor (SRP)
    - Автоматическая регистрация через декоратор
    - Проверка дубликатов ID
    """
    
    _descriptors: Dict[str, RuleDescriptor] = {}
    _rules_by_key: Dict[Tuple[ObservationCategory, str], List[RuleDescriptor]] = {}
    
    @classmethod
    def register(cls, descriptor: RuleDescriptor) -> None:
        """
        Регистрирует правило в реестре.
        
        ES-1.8.1: Проверка дубликатов ID.
        """
        # Проверка дубликатов ID
        if descriptor.id in cls._descriptors:
            existing = cls._descriptors[descriptor.id]
            raise ValueError(
                f"Normalization Rule ID '{descriptor.id}' already registered "
                f"by '{existing.description}'. "
                f"Cannot overwrite with '{descriptor.description}'."
            )
        
        cls._descriptors[descriptor.id] = descriptor
        
        # Индексация по (category, attribute) для быстрого поиска
        key = (descriptor.category, descriptor.attribute)
        if key not in cls._rules_by_key:
            cls._rules_key = {}
            cls._rules_by_key[key] = []
        cls._rules_by_key[key].append(descriptor)
        
        # Сортировка по priority (меньше = выше)
        cls._rules_by_key[key].sort(key=lambda d: d.priority)
    
    @classmethod
    def get_rule(
        cls,
        category: ObservationCategory,
        attribute: str,
        protocol: str = None
    ) -> Optional[RuleDescriptor]:
        """
        Получает правило по категории, атрибуту и опционально протоколу.
        
        ES-1.8.1 (пункт 2): Normalizer не угадывает категорию —
        категория определяется RuleDescriptor.
        """
        key = (category, attribute)
        rules = cls._rules_by_key.get(key, [])
        
        if not rules:
            return None
        
        # Если указан protocol — ищем точное совпадение
        if protocol:
            for rule in rules:
                if rule.protocol == protocol:
                    return rule
        
        # Иначе возвращаем правило с наивысшим приоритетом
        return rules[0] if rules else None
    
    @classmethod
    def get_all_rules(cls) -> List[RuleDescriptor]:
        """Получает все зарегистрированные правила."""
        return list(cls._descriptors.values())
    
    @classmethod
    def get_descriptor(cls, rule_id: str) -> Optional[RuleDescriptor]:
        """Получает дескриптор по ID."""
        return cls._descriptors.get(rule_id)
    
    @classmethod
    def count(cls) -> int:
        """Возвращает количество зарегистрированных правил."""
        return len(cls._descriptors)
    
    @classmethod
    def clear(cls) -> None:
        """Очищает реестр (для тестирования)."""
        cls._descriptors.clear()
        cls._rules_by_key.clear()
    
    @classmethod
    def is_registered(cls, rule_id: str) -> bool:
        """Проверяет, зарегистрировано ли правило."""
        return rule_id in cls._descriptors


# ==============================================================================
# Декоратор для автоматической регистрации
# ==============================================================================

def normalization_rule(
    id: str,
    category: ObservationCategory,
    attribute: str,
    protocol: str,
    priority: int = 100,
    description: str = "",
    version: str = "1.0.0"
):
    """
    Декоратор для автоматической регистрации правила нормализации.
    
    Использование:
        @normalization_rule(
            id="dns.hostname",
            category=ObservationCategory.IDENTITY,
            attribute="hostname",
            protocol="DNS",
            priority=10,
            description="Extract hostname from DNS"
        )
        def normalize_dns_hostname(obs: Observation) -> NormalizationResult:
            return NormalizationResult(value=obs.value.strip().lower())
    """
    def decorator(func: Callable[[Observation], NormalizationResult]):
        descriptor = RuleDescriptor(
            id=id,
            category=category,
            attribute=attribute,
            protocol=protocol,
            priority=priority,
            description=description,
            handler=func,
            version=version
        )
        RuleRegistry.register(descriptor)
        return func
    
    return decorator
