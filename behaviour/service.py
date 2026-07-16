#!/usr/bin/env python3
"""
Behaviour Service — публичный API с инвалидацией кэша.
"""

from __future__ import annotations

from typing import Optional, List, Dict

from .categories import BehaviourCategory
from .models import BehaviourProfile, BehaviourFact, BehaviourExplanation
from .engine import BehaviourEngine
from history import HistoryService
from identity import IdentityService
from session import SessionEngine


class BehaviourService:
    """Публичный API для работы с поведением устройств."""
    
    def __init__(
        self,
        history_service: HistoryService,
        identity_service: IdentityService,
        session_engine: Optional[SessionEngine] = None
    ):
        self.engine = BehaviourEngine(history_service, identity_service, session_engine)
        self.identity_service = identity_service
        self._cache: Dict[str, BehaviourProfile] = {}
        self._identity_versions: Dict[str, int] = {}  # Для инвалидации кэша
    
    def get_profile(self, device_id: str) -> Optional[BehaviourProfile]:
        """Получает BehaviourProfile с проверкой актуальности кэша."""
        # Проверяем, изменилась ли Identity
        identity_profile = self.identity_service.get_identity(device_id)
        current_version = identity_profile.identity_version if identity_profile else 0
        
        if device_id in self._cache and self._identity_versions.get(device_id) == current_version:
            return self._cache[device_id]
        
        # Пересчитываем
        profile = self.engine.analyze(device_id)
        self._cache[device_id] = profile
        self._identity_versions[device_id] = current_version
        
        return profile
    
    def get_best(self, device_id: str, category: BehaviourCategory) -> Optional[BehaviourFact]:
        """Получает лучший факт для категории."""
        profile = self.get_profile(device_id)
        if not profile:
            return None
        
        category_facts = [f for f in profile.facts if f.category == category]
        if not category_facts:
            return None
        
        return max(category_facts, key=lambda x: x.confidence)
    
    def get_ranked(self, device_id: str, category: BehaviourCategory) -> List[BehaviourFact]:
        """Получает ранжированный список фактов для категории."""
        profile = self.get_profile(device_id)
        if not profile:
            return []
        
        category_facts = [f for f in profile.facts if f.category == category]
        return sorted(category_facts, key=lambda x: x.confidence, reverse=True)
    
    def get_all(self) -> List[BehaviourProfile]:
        """Получает все BehaviourProfile."""
        return list(self._cache.values())
    
    def explain(self, device_id: str, category: BehaviourCategory) -> Optional[Dict]:
        """Объясняет поведенческий факт с matched_features."""
        best = self.get_best(device_id, category)
        if not best:
            return None
        
        profile = self.get_profile(device_id)
        
        # Собираем все признаки, участвовавшие в выводе
        matched_features = [best.feature]
        
        return {
            "category": category.value,
            "feature": best.feature,
            "measured_value": best.measured_value,
            "threshold": best.threshold,
            "confidence": best.confidence,
            "raw_score": best.raw_score,
            "status": best.status.value,
            "rule_id": best.rule_id,
            "matched_rules": best.matched_rules,
            "matched_features": matched_features,
            "reasons": best.reasons,
            "feature_coverage": profile.feature_coverage if profile else 0.0,
            "behaviour_coverage": profile.behaviour_coverage if profile else 0.0
        }
    
    def statistics(self, device_id: str) -> Optional[Dict]:
        """Возвращает статистику поведения."""
        profile = self.get_profile(device_id)
        if not profile:
            return None
        
        return {
            "facts_total": profile.summary.facts_total,
            "high": profile.summary.high,
            "medium": profile.summary.medium,
            "low": profile.summary.low,
            "unknown": profile.summary.unknown,
            "feature_coverage": profile.feature_coverage,
            "behaviour_coverage": profile.behaviour_coverage
        }
    
    def refresh(self, device_id: str) -> Optional[BehaviourProfile]:
        """Пересчитывает BehaviourProfile."""
        if device_id in self._cache:
            del self._cache[device_id]
        if device_id in self._identity_versions:
            del self._identity_versions[device_id]
        return self.get_profile(device_id)
    
    def refresh_all(self) -> List[BehaviourProfile]:
        """Пересчитывает все BehaviourProfile."""
        self._cache.clear()
        self._identity_versions.clear()
        return self.get_all()
        
    def debug(self, device_id: str) -> Optional[DebugInfo]:
        """Возвращает отладочную информацию."""
        _, debug = self.engine.analyze(device_id)
        return debug
