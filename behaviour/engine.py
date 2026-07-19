#!/usr/bin/env python3
"""Behaviour Engine — координация FeatureBuilder и Evaluator."""
from __future__ import annotations
import time
from typing import List, Optional, Tuple
from .models import BehaviourProfile, FeatureSet, BehaviourSummary, SourceVersions, DebugInfo
from .features import FeatureBuilder
from .evaluator import BehaviourEvaluator
from history import HistoryService
from identity import IdentityService
from session import SessionEngine

# v1.6.9.2: Configuration Layer Integration
from configuration import ConfigurationManager


class BehaviourEngine:
    """
    Координирует вычисление признаков и оценку поведения.
    
    v1.6.9.2: Принимает ConfigurationManager через конструктор (Dependency Injection).
    """
    
    def __init__(
        self,
        history_service: HistoryService,
        identity_service: IdentityService,
        session_engine: Optional[SessionEngine] = None,
        configuration: Optional[ConfigurationManager] = None  # v1.6.9.2: DI
    ):
        self.feature_builder = FeatureBuilder(history_service, identity_service, session_engine)
        self.evaluator = BehaviourEvaluator()
        self.configuration = configuration  # v1.6.9.2: Configuration через DI
    
    def analyze(self, device_id: str) -> Tuple[BehaviourProfile, DebugInfo]:
        """
        Анализирует поведение устройства.
        
        Returns:
            Tuple[BehaviourProfile, DebugInfo]
        """
        start_time = time.time()
        
        # 1. Вычисляем сырые признаки
        features = self.feature_builder.build(device_id)
        
        # 2. Применяем правила (БЕЗ лишних аргументов!)
        facts, debug_info = self.evaluator.evaluate(features)
        
        # 3. Вычисляем coverage
        feature_coverage = self._calculate_feature_coverage(features)
        behaviour_coverage = self._calculate_behaviour_coverage(facts)
        
        # 4. Формируем summary
        summary = self._build_summary(facts)
        
        # 5. Создаём profile
        profile = BehaviourProfile(
            identity_id=device_id,
            generated_at=features.generated_at,
            engine_version="1.0.0",
            rules_version="1.0.0",
            feature_version="1.0.0",
            provider_version="1.0.0",
            metric_coverage=0.0,  # Behaviour не имеет метрик
            feature_coverage=feature_coverage,
            rule_match_ratio=behaviour_coverage,
            behaviour_coverage=behaviour_coverage,
            features=features,
            facts=facts,
            summary=summary,
            source_versions=SourceVersions()
        )
        
        # 6. Заполняем debug_info
        debug_info.computation_time_ms = (time.time() - start_time) * 1000
        debug_info.cache_hit = False
        debug_info.cache_key = ()
        
        return profile, debug_info
    
    def _calculate_feature_coverage(self, features: FeatureSet) -> float:
        """Вычисляет процент успешно вычисленных признаков."""
        total_features = 10
        filled_features = sum([
            features.average_session_duration is not None,
            features.session_count > 0,
            features.peak_speed is not None,
            features.average_speed is not None,
            features.total_traffic > 0,
            features.idle_ratio > 0,
            features.active_ratio > 0,
            features.ap_changes > 0,
            features.ssid_changes > 0,
            features.lifetime_seconds is not None
        ])
        return (filled_features / total_features) * 100.0
    
    def _calculate_behaviour_coverage(self, facts: List) -> float:
        """Вычисляет процент определённых моделей поведения."""
        from .categories import BehaviourCategory
        
        total_categories = len(BehaviourCategory)
        unique_categories = set(f.category for f in facts)
        filled_categories = len(unique_categories)
        
        return (filled_categories / total_categories) * 100.0 if total_categories > 0 else 0.0
    
    def _build_summary(self, facts: List) -> BehaviourSummary:
        """Формирует краткую сводку."""
        from .categories import BehaviourStatus
        
        summary = BehaviourSummary()
        
        for fact in facts:
            summary.facts_total += 1
            
            if fact.status in (BehaviourStatus.CONFIRMED, BehaviourStatus.HIGH):
                summary.high += 1
            elif fact.status == BehaviourStatus.MEDIUM:
                summary.medium += 1
            elif fact.status == BehaviourStatus.LOW:
                summary.low += 1
            else:
                summary.unknown += 1
        
        return summary
