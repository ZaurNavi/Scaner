#!/usr/bin/env python3
"""Evaluator работает ТОЛЬКО с FeatureSet."""
from typing import List, Dict, Any, Tuple
from .models import BehaviourFact, DebugInfo
from .categories import BehaviourStatus
from .rules import get_enabled_rules, evaluate_condition

class BehaviourEvaluator:
    def evaluate(self, feature_set) -> Tuple[List[BehaviourFact], DebugInfo]:
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
            # Безопасно получаем ID правила (может быть 'id' или 'rule_id')
            rule_id = getattr(rule, 'rule_id', getattr(rule, 'id', 'UNKNOWN'))
            
            # Получаем имя метрики
            metric_name = getattr(rule, 'metric', None)
            if not metric_name:
                continue
                
            feature_value = getattr(feature_set, metric_name, None)
            
            if feature_value is None:
                debug_info.skipped_rules.append(f"{rule_id} (Missing metric: {metric_name})")
                continue

            debug_info.evaluated_rules.append(rule_id)
            
            # Безопасно получаем остальные атрибуты правила
            condition = getattr(rule, 'condition', None) or getattr(rule, 'operator', None)
            threshold = getattr(rule, 'threshold', None)
            weight = getattr(rule, 'weight', 0)
            category = getattr(rule, 'category', None)
            name = getattr(rule, 'name', 'Unknown Rule')
            
            if condition and evaluate_condition(condition, feature_value, threshold):
                debug_info.matched_rules.append(rule_id)
                confidence = min((weight / 100.0) * 100, 100.0)
                status = BehaviourStatus.HIGH if confidence >= 60 else BehaviourStatus.MEDIUM
                
                facts.append(BehaviourFact(
                    category=category,
                    feature=metric_name,
                    value=feature_value,
                    measured_value=feature_value,
                    threshold=threshold,
                    score=weight,
                    raw_score=weight,
                    confidence=confidence,
                    status=status,
                    rule_id=rule_id,
                    matched_rules=[rule_id],
                    sources=["behaviour_engine"],
                    reasons=[f"{name}: {feature_value} {condition} {threshold}"]
                ))
                
        return facts, debug_info
