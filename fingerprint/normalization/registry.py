#!/usr/bin/env python3
"""
Rule Registry — реестр правил нормализации.
ES-1.8.1: Автоматическая регистрация правил.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Type

from .models import Observation, ObservationCategory


@dataclass
class NormalizationRule:
    """
    Правило нормализации.
    
    ES-1.8.1: Каждое правило отвечает только за одно поле.
    """
    category: ObservationCategory
    attribute: str
    handler: Callable[[Observation], any]
    priority: int = 100
    description: str = ""


class RuleRegistry:
    """
    Реестр правил нормализации.
    
    ES-1.8.1: Автоматическая регистрация через декоратор.
    Движок ничего не знает о DNS, mDNS и т.д.
    """
    
    _rules: Dict[Tuple[ObservationCategory, str], NormalizationRule] = {}
    
    @classmethod
    def register(
        cls,
        category: ObservationCategory,
        attribute: str,
        handler: Callable[[Observation], any],
        priority: int = 100,
        description: str = ""
    ) -> None:
        """
        Регистрирует правило нормализации.
        
        Args:
            category: Категория наблюдения
            attribute: Атрибут (например, "hostname")
            handler: Функция-обработчик
            priority: Приоритет (меньше = выше)
            description: Описание правила
        """
        key = (category, attribute)
        
        if key in cls._rules:
            existing = cls._rules[key]
            # Если новое правило имеет выше приоритет, заменяем
            if priority < existing.priority:
                cls._rules[key] = NormalizationRule(
                    category=category,
                    attribute=attribute,
                    handler=handler,
                    priority=priority,
                    description=description
                )
        else:
            cls._rules[key] = NormalizationRule(
                category=category,
                attribute=attribute,
                handler=handler,
                priority=priority,
                description=description
            )
    
    @classmethod
    def get_rule(
        cls,
        category: ObservationCategory,
        attribute: str
    ) -> Optional[NormalizationRule]:
        """Получает правило по категории и атрибуту."""
        return cls._rules.get((category, attribute))
    
    @classmethod
    def get_all_rules(cls) -> List[NormalizationRule]:
        """Получает все зарегистрированные правила."""
        return list(cls._rules.values())
    
    @classmethod
    def count(cls) -> int:
        """Возвращает количество зарегистрированных правил."""
        return len(cls._rules)
    
    @classmethod
    def clear(cls) -> None:
        """Очищает реестр (для тестирования)."""
        cls._rules.clear()


def normalization_rule(
    category: ObservationCategory,
    attribute: str,
    priority: int = 100,
    description: str = ""
):
    """
    Декоратор для автоматической регистрации правила нормализации.
    
    Использование:
        @normalization_rule(
            category=ObservationCategory.IDENTITY,
            attribute="hostname",
            priority=10,
            description="Extract hostname from DNS"
        )
        def normalize_hostname(obs: Observation) -> str:
            return obs.value
    """
    def decorator(func: Callable[[Observation], any]):
        RuleRegistry.register(
            category=category,
            attribute=attribute,
            handler=func,
            priority=priority,
            description=description
        )
        return func
    
    return decorator
