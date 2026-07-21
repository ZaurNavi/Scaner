#!/usr/bin/env python3
"""
Normalizer — преобразование Observation в UnifiedObservation.
ES-1.8.3: Rule выбирается ТОЛЬКО по attribute.
"""

from __future__ import annotations

from typing import Iterator, List, Optional

from configuration import ConfigurationManager

from .models import (
    Observation,
    ObservationCategory,
    ObservationMetadata,
    UnifiedObservation,
)
from .registry import RuleRegistry


class Normalizer:
    """
    Преобразует Observation в UnifiedObservation.
    """
    
    def __init__(self, configuration: ConfigurationManager):
        self.config = configuration
        self.unknown_policy = self.config.get(
            "fingerprint.normalization.unknown_policy",
            "log"  # keep, drop, log
        )
    
    def normalize(
        self,
        observation: Observation,
        category: ObservationCategory
    ) -> Optional[UnifiedObservation]:
        """
        Нормализует одну Observation.
        ES-1.8.3: Правило выбирается ТОЛЬКО по attribute.
        """
        # ES-1.8.3: Ищем правило ТОЛЬКО по attribute
        rule = RuleRegistry.get_rule(attribute=observation.attribute)
        
        if rule is None:
            # Unknown policy
            if self.unknown_policy == "drop":
                return None
            elif self.unknown_policy == "log":
                print(f"      [NORMALIZER] ⚠️ No rule for {category.value}.{observation.attribute}")
                normalized_value = observation.value
                confidence = 0.5
                warnings = ("no_rule",)
            else:  # keep
                normalized_value = observation.value
                confidence = 0.5
                warnings = ("no_rule", "kept")
        else:
            # Применяем правило
            try:
                result = rule.apply(observation)
                normalized_value = result.value
                confidence = result.confidence
                warnings = result.warnings
            except Exception as e:
                print(f"      [NORMALIZER] ❌ Rule '{rule.id}' failed: {e}")
                normalized_value = observation.value
                confidence = 0.0
                warnings = (f"rule_failed:{e}",)
        
        # Создаём UnifiedObservation
        return UnifiedObservation(
            observation_id=observation.observation_id,
            collector_id=observation.collector_id,
            protocol=observation.protocol,
            category=category,
            attribute=observation.attribute,
            normalized_value=normalized_value,
            confidence=confidence,
            timestamp=observation.timestamp,
            warnings=warnings,
            metadata=observation.metadata
        )
    
    def normalize_many(
        self,
        observations: List[Observation],
        category_map: dict[str, ObservationCategory] = None
    ) -> List[UnifiedObservation]:
        """
        Нормализует множество Observation (Batch API).
        """
        results = []
        for obs in observations:
            # Определяем категорию
            if category_map and obs.collector_id in category_map:
                category = category_map[obs.collector_id]
            else:
                # Fallback: используем IDENTITY как дефолт
                category = ObservationCategory.IDENTITY
            
            unified = self.normalize(obs, category)
            if unified is not None:
                results.append(unified)
        return results
    
    def normalize_stream(
        self,
        observations: Iterator[Observation],
        category_map: dict[str, ObservationCategory] = None
    ) -> Iterator[UnifiedObservation]:
        """
        Потоковая нормализация.
        """
        for obs in observations:
            if category_map and obs.collector_id in category_map:
                category = category_map[obs.collector_id]
            else:
                category = ObservationCategory.IDENTITY
            
            unified = self.normalize(obs, category)
            if unified is not None:
                yield unified
