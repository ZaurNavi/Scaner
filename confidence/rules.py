#!/usr/bin/env python3
"""
Декларативные правила оценки достоверности.
Никакой жёстко закодированной логики по конкретным брендам или моделям.

v1.6.9.5: ConfidenceRules — сервис с Dependency Injection.
"""

from .categories import FactCategory

# v1.6.9.5: Configuration Layer Integration
from configuration import ConfigurationManager


class ConfidenceRules:
    """
    Сервис правил оценки достоверности.
    
    v1.6.9.5: Принимает ConfigurationManager через конструктор (Dependency Injection).
    Кэширует конфигурацию для производительности.
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        Конструктор с Dependency Injection.
        
        Args:
            configuration: Единый источник конфигурации
        """
        self.configuration = configuration
    
    def get_weight(self, category: FactCategory, source: str) -> int:
        """
        Возвращает вес для конкретной категории и источника.
        
        Args:
            category: Категория факта (VENDOR, MODEL, etc.)
            source: Источник данных (omada, mdns, etc.)
        
        Returns:
            int: Вес (0 если параметр не найден)
        """
        param_id = f"confidence.weight.{category.value}.{source}"
        
        try:
            return self.configuration.get(param_id, 0)
        except Exception:
            # Если параметр не найден — возвращаем 0
            return 0
    
    def get_rules_for_category(self, category: FactCategory) -> list:
        """
        Возвращает все правила для указанной категории.
        
        Args:
            category: Категория факта
        
        Returns:
            list: Список кортежей (source, weight)
        """
        rules = []
        
        # Получаем все параметры группы "Confidence"
        try:
            confidence_params = self.configuration.group("Confidence")
            
            # Фильтруем только веса для данной категории
            prefix = f"confidence.weight.{category.value}."
            for param_id, value in confidence_params.items():
                if param_id.startswith(prefix):
                    source = param_id[len(prefix):]
                    rules.append((source, value))
        except Exception:
            pass
        
        return rules
