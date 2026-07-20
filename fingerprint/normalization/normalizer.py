#!/usr/bin/env python3
"""
Normalizer — преобразование Observation в UnifiedObservation.
ES-1.8.1: Единый конвейер нормализации.
"""

from __future__ import annotations

from typing import List, Optional

from configuration import ConfigurationManager

from .models import Observation, ObservationCategory, UnifiedObservation
from .registry import RuleRegistry


class Normalizer:
    """
    Преобразует Observation в UnifiedObservation.
    
    ES-1.8.1: Batch API — normalize() и normalize_many().
    Dependency Injection через ConfigurationManager.
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        v1.8.1: Dependency Injection через ConfigurationManager.
        
        Args:
            configuration: ConfigurationManager для получения настроек
        """
        self.config = configuration
        self.unknown_policy = self.config.get(
            "fingerprint.normalization.unknown_policy",
            "log"  # keep, drop, log
        )
    
    def normalize(self, observation: Observation) -> Optional[UnifiedObservation]:
        """
        Нормализует одну Observation.
        
        Args:
            observation: Сырая Observation
        
        Returns:
            UnifiedObservation или None (если unknown_policy == "drop")
        """
        # Определяем категорию из metadata или protocol
        category = self._infer_category(observation)
        
        # Ищем правило для этой категории и атрибута
        rule = RuleRegistry.get_rule(category, observation.attribute)
        
        if rule is None:
            # Unknown policy
            if self.unknown_policy == "drop":
                return None
            elif self.unknown_policy == "log":
                print(f"      [NORMALIZER] ⚠️ No rule for {category.value}.{observation.attribute}")
                # Используем значение как есть
                normalized_value = observation.value
            else:  # keep
                normalized_value = observation.value
        else:
            # Применяем правило
            try:
                normalized_value = rule.handler(observation)
            except Exception as e:
                print(f"      [NORMALIZER] ❌ Rule failed for {category.value}.{observation.attribute}: {e}")
                normalized_value = observation.value
        
        # Создаём UnifiedObservation
        return UnifiedObservation(
            observation_id=observation.observation_id,
            collector_id=observation.collector_id,
            protocol=observation.protocol,
            transport=observation.transport,
            category=category,
            attribute=observation.attribute,
            normalized_value=normalized_value,
            timestamp=observation.timestamp,
            metadata=observation.metadata
        )
    
    def normalize_many(self, observations: List[Observation]) -> List[UnifiedObservation]:
        """
        Нормализует множество Observation.
        
        ES-1.8.1: Batch API для обработки больших пакетов.
        
        Args:
            observations: Список сырых Observation
        
        Returns:
            Список UnifiedObservation
        """
        results = []
        for obs in observations:
            unified = self.normalize(obs)
            if unified is not None:
                results.append(unified)
        return results
    
    def _infer_category(self, observation: Observation) -> ObservationCategory:
        """
        Определяет категорию из metadata или protocol.
        
        ES-1.8.1: Если категория не указана, пытаемся определить.
        """
        # Проверяем metadata
        if "category" in observation.metadata:
            cat_value = observation.metadata["category"]
            if isinstance(cat_value, ObservationCategory):
                return cat_value
            try:
                return ObservationCategory(cat_value)
            except ValueError:
                pass
        
        # Определяем по protocol
        protocol_map = {
            "DNS": ObservationCategory.IDENTITY,
            "mDNS": ObservationCategory.IDENTITY,
            "LLMNR": ObservationCategory.IDENTITY,
            "NBNS": ObservationCategory.IDENTITY,
            "DHCP": ObservationCategory.NETWORK,
            "SSDP": ObservationCategory.SERVICE,
            "HTTP": ObservationCategory.APPLICATION,
            "TLS": ObservationCategory.SECURITY,
        }
        
        return protocol_map.get(observation.protocol, ObservationCategory.IDENTITY)
