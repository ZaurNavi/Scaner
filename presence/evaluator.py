#!/usr/bin/env python3
"""Evaluator работает ТОЛЬКО с PresenceFeatureSet."""
from typing import List, Dict, Any, Tuple
from .models import PresenceFeatureSet, PresenceFact
from .categories import PresenceStatus
from .rules import get_enabled_rules, evaluate_condition

class PresenceEvaluator:
    def evaluate(self, feature_set: PresenceFeatureSet) -> Tuple[List[PresenceFact], Dict]:
        facts = []
        rules = get_enabled_rules()
        
        debug_info = {"evaluated": [], "matched": [], "skipped": [], "all_rules": rules}

        for rule in rules:
            missing_features = [
                f for f in rule.required_features 
                if f not in feature_set or not feature_set[f].availability.available
            ]
            if missing_features:
                debug_info["skipped"].append(f"{rule.id} (Missing features: {missing_features})")
                continue

            debug_info["evaluated"].append(rule.id)
            target_feature = rule.required_features[0]
            feature = feature_set[target_feature]
            
            if evaluate_condition(rule.operator, feature.value, rule.threshold):
                debug_info["matched"].append(rule.id)
                confidence = min((rule.weight / 100.0) * 100, 100.0)
                status = PresenceStatus.HIGH if confidence >= 60 else PresenceStatus.MEDIUM
                
                facts.append(PresenceFact(
                    category=rule.category,
                    feature=target_feature,
                    value=rule.category.value,
                    measured_value=feature.value,
                    score=rule.weight,
                    confidence=confidence,
                    status=status,
                    matched_rules=[rule.id],
                    sources=feature.sources,
                    reasons=[f"{rule.name}: {feature.value} {rule.operator} {rule.threshold}"]
                ))
                
        return facts, debug_info
