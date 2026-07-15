#!/usr/bin/env python3
"""
Evaluator — применение правил к FeatureSet.
Хранит measured_value, threshold, rule_id в BehaviourFact.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from .categories import BehaviourCategory, BehaviourStatus
from .models import (
    BehaviourFact, BehaviourProfile, BehaviourSummary,
    FeatureSet, SourceVersions
)
from .rules import get_enabled_rules, evaluate_condition
from .normalizer import normalize_score
from .constants import ENGINE_VERSION, RULES_VERSION


class BehaviourEvaluator:
    """Применяет правила к FeatureSet и формирует BehaviourProfile."""
    
    def evaluate(self, device_id: str, features: FeatureSet, source_versions: SourceVersions = None) -> BehaviourProfile:
        """
        Оценивает поведение устройства на основе признаков.
        """
        profile = BehaviourProfile(
            identity_id=device_id,
            generated_at=datetime.now(),
            engine_version=ENGINE_VERSION,
            rules_version=RULES_VERSION,
            features=features,
            source_versions=source_versions or SourceVersions()
        )
        
        # Применяем все правила
        rules = get_enabled_rules()
        for rule in rules:
            metric_value = getattr(features, rule.metric, None)
            
            if evaluate_condition(rule.operator, metric_value, rule.threshold):
                # Правило сработало — создаём факт с measured_value
                threshold_display = rule.threshold.value if rule.threshold.value else f"{rule.threshold.min}-{rule.threshold.max}"
                
                profile.facts.append(
                    BehaviourFact(
                        category=rule.category,
                        feature=rule.metric,
                        measured_value=metric_value,
                        threshold=threshold_display,
                        raw_score=rule.weight,
                        rule_id=rule.rule_id,
                        matched_rules=[rule.rule_id],
                        reasons=[f"+{rule.weight} {rule.description}"]
                    )
                )
        
        # Нормализуем все факты
        for fact in profile.facts:
            fact.confidence = normalize_score(fact.raw_score)
            fact.status = self._determine_status(fact.confidence)
        
        # Вычисляем coverage
        profile.feature_coverage = self._calculate_feature_coverage(features)
        profile.behaviour_coverage = self._calculate_behaviour_coverage(profile.facts)
        
        # Формируем summary
        profile.summary = self._build_summary(profile.facts)
        
        return profile
    
    def _determine_status(self, confidence: float) -> BehaviourStatus:
        """Определяет статус на основе confidence."""
        if confidence >= 80.0:
            return BehaviourStatus.CONFIRMED
        elif confidence >= 60.0:
            return BehaviourStatus.HIGH
        elif confidence >= 40.0:
            return BehaviourStatus.MEDIUM
        elif confidence >= 20.0:
            return BehaviourStatus.LOW
        else:
            return BehaviourStatus.UNKNOWN
    
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
    
    def _calculate_behaviour_coverage(self, facts: List[BehaviourFact]) -> float:
        """Вычисляет процент определённых моделей поведения."""
        total_categories = len(BehaviourCategory)
        filled_categories = len(set(f.category for f in facts))
        
        return (filled_categories / total_categories) * 100.0 if total_categories > 0 else 0.0
    
    def _build_summary(self, facts: List[BehaviourFact]) -> BehaviourSummary:
        """Формирует краткую сводку."""
        summary = BehaviourSummary(generated_at=datetime.now())
        
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
