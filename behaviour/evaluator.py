#!/usr/bin/env python3
"""Evaluator работает ТОЛЬКО с FeatureSet."""
from typing import List, Dict, Any, Tuple
from .models import BehaviourFact, DebugInfo  # <-- ИСПРАВЛЕНО: убран BehaviourFeatureSet
from .categories import BehaviourStatus
from .rules import get_enabled_rules, evaluate_condition

class BehaviourEvaluator:
    def evaluate(self, feature_set, metrics: Dict[str, Any] = None) -> Tuple[List[BehaviourFact], DebugInfo]:
        facts = []
        rules = get_enabled_rules()
        
        debug_info = DebugInfo(
            computation_time_ms=0.0,
            provider_times={},
            builder_times={},
            feature_times={},
            evaluated_rules=[],
            matched_rules=[],
            skipped_rules=[],
            missing_features=[],
            cache_invalidated=False,
            cache_reason="",
            cache_hit=False,
            cache_key=(),
            engine_version="1.0.0",
            feature_version="1.0.0",
            provider_version="1.0.0"
        )

        for rule in rules:
            # Rule знает только Features
            missing_features = [
                f for f in rule.required_features 
                if not hasattr(feature_set, f) or getattr(feature_set, f) is None
            ]
            if missing_features:
                debug_info.skipped_rules.append(f"{rule.id} (Missing features: {missing_features})")
                continue

            debug_info.evaluated_rules.append(rule.id)
            target_feature = rule.required_features[0]
            feature_value = getattr(feature_set, target_feature, None)
            
            if evaluate_condition(rule.operator, feature_value, rule.threshold):
                debug_info.matched_rules.append(rule.id)
                confidence = min((rule.weight / 100.0) * 100, 100.0)
                status = BehaviourStatus.HIGH if confidence >= 60 else BehaviourStatus.MEDIUM
                
                facts.append(BehaviourFact(
                    category=rule.category,
                    feature=target_feature,
                    value=feature_value,
                    measured_value=feature_value,
                    threshold=rule.threshold,
                    score=rule.weight,
                    raw_score=rule.weight,
                    confidence=confidence,
                    status=status,
                    rule_id=rule.id,
                    matched_rules=[rule.id],
                    sources=["behaviour_engine"],
                    reasons=[f"{rule.name}: {feature_value} {rule.operator} {rule.threshold}"]
                ))
                
        return facts, debug_info
