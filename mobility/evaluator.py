#!/usr/bin/env python3
"""Evaluator работает ТОЛЬКО с MobilityFeatureSet."""
from typing import List
from .models import MobilityFeatureSet, MobilityFact, MobilityTimeline
from .categories import MobilityStatus
from .rules import get_enabled_rules, evaluate_condition

class MobilityEvaluator:
    def evaluate(self, feature_set: MobilityFeatureSet, timeline: MobilityTimeline) -> List[MobilityFact]:
        facts = []
        rules = get_enabled_rules()
        
        for rule in rules:
            # Проверяем доступность всех требуемых фич
            missing = [f for f in rule.required_features if f not in feature_set or not feature_set[f].availability.available]
            if missing:
                continue # Пропускаем правило, если нет данных
            
            # Берем значение первой требуемой фичи для оценки (упрощение для примера)
            target_feature = rule.required_features[0]
            feature = feature_set[target_feature]
            
            if evaluate_condition(rule.operator, feature.value, rule.threshold):
                confidence = min((rule.weight / 100.0) * 100, 100.0)
                status = MobilityStatus.HIGH if confidence >= 60 else MobilityStatus.MEDIUM
                
                facts.append(MobilityFact(
                    category=rule.category,
                    feature=target_feature,
                    value=rule.category.value,
                    measured_value=feature.value,
                    score=rule.weight,
                    confidence=confidence,
                    status=status,
                    matched_rules=[rule.id],
                    sources=feature.sources,
                    reason=f"{rule.name}: {feature.value} {rule.operator} {rule.threshold}"
                ))
        return facts
