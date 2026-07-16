#!/usr/bin/env python3
"""Coverage Calculator для Behaviour Engine."""
from typing import Dict, Any
from ..coverage.platform import Coverage
from ..registry.feature_registry import FeatureRegistry
from ..registry.rule_registry import RuleRegistry

class BehaviourCoverageCalculator:
    """Вычисляет Coverage для Behaviour Engine."""
    
    @staticmethod
    def calculate(
        metrics: Dict[str, Any],
        features: Dict[str, Any],
        rules_evaluated: int,
        rules_matched: int,
        facts_count: int
    ) -> Coverage:
        """Вычисляет все типы Coverage."""
        
        # Metric Coverage: 10 зарегистрированных метрик
        total_metrics = 10
        computed_metrics = len(metrics)
        metric_coverage = (computed_metrics / total_metrics * 100) if total_metrics > 0 else 0.0
        
        # Feature Coverage: 11 зарегистрированных фич
        total_features = 11
        computed_features = len(features)
        feature_coverage = (computed_features / total_features * 100) if total_features > 0 else 0.0
        
        # Rule Coverage: 7 правил
        total_rules = 7
        rule_coverage = (rules_evaluated / total_rules * 100) if total_rules > 0 else 0.0
        
        # Fact Coverage
        fact_coverage = (facts_count / total_rules * 100) if total_rules > 0 else 0.0
        
        return Coverage(
            timeline_coverage=100.0,
            metric_coverage=metric_coverage,
            feature_coverage=feature_coverage,
            rule_coverage=rule_coverage,
            fact_coverage=fact_coverage
        )
