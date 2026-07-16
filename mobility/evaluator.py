#!/usr/bin/env python3
"""Evaluator работает ТОЛЬКО с MobilityFeatureSet и metrics."""
from typing import List, Dict, Any, Tuple
from .models import MobilityFeatureSet, MobilityFact
from .categories import MobilityStatus
from .rules import get_enabled_rules, evaluate_condition

class MobilityEvaluator:
    def evaluate(self, feature_set: MobilityFeatureSet, metrics: Dict[str, Any]) -> Tuple[List[MobilityFact], Dict]:
        facts = []
        rules = get_enabled_rules()
        
        debug_info = {"evaluated": [], "matched": [], "skipped": [], "all_rules": rules}

        for rule in rules:
            # Проверка доступности провайдеров (Замечание №6)
            missing_providers = [p for p in rule.required_providers if p not in metrics]
            if missing_providers:
                debug_info["skipped"].append(f"{rule.id} (Missing providers: {missing_providers})")
                continue

            # Проверка доступности фич
            missing_features = [f for f in rule.required_features if f not in feature_set or not feature_set[f].availability.available]
            if missing_features:
                debug_info["skipped"].append(f"{rule.id} (Missing features: {missing_features})")
                continue

            debug_info["evaluated"].append(rule.id)
            target_feature = rule.required_features[0]
            feature = feature_set[target_feature]
            
            if evaluate_condition(rule.operator, feature.value, rule.threshold):
                debug_info["matched"].append(rule.id)
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
                    reasons=[f"{rule.name}: {feature.value} {rule.operator} {rule.threshold}"] # <-- ИСПРАВЛЕНО: список
                ))
                
        return facts, debug_info
