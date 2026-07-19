#!/usr/bin/env python3
"""
Confidence Service — публичный API для оценки достоверности.

v1.6.9.5: Принимает ConfigurationManager через конструктор (Dependency Injection).
"""

from __future__ import annotations

from typing import Optional, List, Dict

from .categories import FactCategory
from .models import ConfidenceProfile, FactAssessment
from .evaluator import ConfidenceEvaluator
from .rules import ConfidenceRules
from identity import IdentityService

# v1.6.9.5: Configuration Layer Integration
from configuration import ConfigurationManager


class ConfidenceService:
    """Публичный API для работы с Confidence."""
    
    def __init__(
        self,
        identity_service: IdentityService,
        configuration: Optional[ConfigurationManager] = None
    ):
        """
        v1.6.9.5: Конструктор с Dependency Injection.
        
        Args:
            identity_service: Сервис identity
            configuration: Конфигурация (если None — используется глобальный Singleton)
        """
        self.identity_service = identity_service
        
        # v1.6.9.5: Создаём ConfidenceRules с переданной конфигурацией
        if configuration is not None:
            rules = ConfidenceRules(configuration)
            self.evaluator = ConfidenceEvaluator(rules=rules)
        else:
            # Fallback: используем глобальный Singleton (для обратной совместимости)
            self.evaluator = ConfidenceEvaluator()
        
        self._cache: Dict[str, ConfidenceProfile] = {}
    
    def get_profile(self, identity_id: str) -> Optional[ConfidenceProfile]:
        """Получает ConfidenceProfile для устройства."""
        if identity_id in self._cache:
            return self._cache[identity_id]
        
        identity_profile = self.identity_service.get_identity(identity_id)
        if not identity_profile:
            return None
        
        confidence_profile = self.evaluator.evaluate(identity_profile)
        self._cache[identity_id] = confidence_profile
        
        return confidence_profile
    
    def get_best(self, identity_id: str, category: FactCategory) -> Optional[FactAssessment]:
        """Получает лучшую оценку для категории."""
        profile = self.get_profile(identity_id)
        if not profile or category not in profile.facts:
            return None
        
        assessments = profile.facts[category]
        if not assessments:
            return None
        
        return max(assessments, key=lambda x: x.confidence)
    
    def get_ranked(self, identity_id: str, category: FactCategory) -> List[FactAssessment]:
        """Получает ранжированный список альтернатив для категории."""
        profile = self.get_profile(identity_id)
        if not profile or category not in profile.facts:
            return []
        
        return sorted(profile.facts[category], key=lambda x: x.confidence, reverse=True)
    
    def get_all(self) -> List[ConfidenceProfile]:
        """Получает все ConfidenceProfile."""
        # Получаем все identity
        # TODO: Реализовать list_identities() в IdentityService
        return list(self._cache.values())
    
    def explain(self, identity_id: str, category: FactCategory) -> Optional[Dict]:
        """Объясняет оценку для категории."""
        best = self.get_best(identity_id, category)
        if not best:
            return None
        
        return {
            "category": category.value,
            "value": best.value,
            "confidence": best.confidence,
            "raw_score": best.raw_score,
            "reasons": best.reasons,
            "sources": best.sources,
            "status": best.status.value
        }
    
    def statistics(self, identity_id: str) -> Optional[Dict]:
        """Возвращает статистику оценок."""
        profile = self.get_profile(identity_id)
        if not profile:
            return None
        
        return {
            "total_facts": profile.statistics.total_facts,
            "evaluated": profile.statistics.evaluated,
            "conflicts": profile.statistics.conflicts,
            "insufficient_data": profile.statistics.insufficient_data,
            "unknown": profile.statistics.unknown,
            "coverage": profile.coverage
        }
    
    def refresh(self, identity_id: str) -> Optional[ConfidenceProfile]:
        """Пересчитывает ConfidenceProfile."""
        if identity_id in self._cache:
            del self._cache[identity_id]
        return self.get_profile(identity_id)
    
    def refresh_all(self) -> List[ConfidenceProfile]:
        """Пересчитывает все ConfidenceProfile."""
        self._cache.clear()
        return self.get_all()
