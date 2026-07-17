#!/usr/bin/env python3
"""Coverage Builder — агрегирует Coverage из всех EngineResult."""
from typing import List, Any, Dict
from ...coverage.platform import Coverage

class CoverageBuilder:
    """Строит Coverage для Knowledge Snapshot."""
    
    @staticmethod
    def build(engine_results: Dict[str, Any]) -> Coverage:
        """
        Строит Coverage из EngineResult всех движков.
        
        ИСПРАВЛЕНО: агрегирует реальные Coverage, а не хардкодит 100%.
        
        Args:
            engine_results: Dict[engine_name, EngineResult]
        """
        if not engine_results:
            return Coverage(
                timeline_coverage=0.0,
                metric_coverage=0.0,
                feature_coverage=0.0,
                rule_coverage=0.0,
                fact_coverage=0.0
            )
        
        # Агрегируем Coverage из всех движков
        timeline_coverages = []
        metric_coverages = []
        feature_coverages = []
        rule_coverages = []
        fact_coverages = []
        
        for engine_name, result in engine_results.items():
            if hasattr(result, 'coverage'):
                cov = result.coverage
                timeline_coverages.append(cov.timeline_coverage)
                metric_coverages.append(cov.metric_coverage)
                feature_coverages.append(cov.feature_coverage)
                rule_coverages.append(cov.rule_coverage)
                fact_coverages.append(cov.fact_coverage)
        
        # Среднее по всем движкам
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0.0
        
        return Coverage(
            timeline_coverage=avg(timeline_coverages),
            metric_coverage=avg(metric_coverages),
            feature_coverage=avg(feature_coverages),
            rule_coverage=avg(rule_coverages),
            fact_coverage=avg(fact_coverages)
        )
