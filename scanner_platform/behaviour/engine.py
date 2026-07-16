#!/usr/bin/env python3
"""
Behaviour Engine — первый движок на платформенной архитектуре Core.

Архитектура:
    Timeline → Metric Registry → Metrics → Feature Registry → Features → 
    Rule Registry → Rules → Platform Facts → Engine Result
"""
import time
from typing import Dict, Any
from datetime import datetime

from ..timeline.models import Timeline
from ..registry.metric_registry import MetricRegistry
from ..registry.feature_registry import FeatureRegistry
from ..registry.rule_registry import RuleRegistry
from ..builders.facts_builder import FactsBuilder
from ..cache.platform import VersionSnapshot

from .models import EngineResult, EngineStatistics
from .coverage import BehaviourCoverageCalculator
from .explain import BehaviourExplainBuilder
from .registry import register_all

class BehaviourEngine:
    """
    Behaviour Engine на платформенной архитектуре.
    
    Использует ТОЛЬКО:
    - Metric Registry
    - Feature Registry
    - Rule Registry
    - Fact Builder
    """
    
    def __init__(self):
        # Регистрируем все компоненты движка
        register_all()
        self.facts_builder = FactsBuilder(engine_name="behaviour")
        self.coverage_calculator = BehaviourCoverageCalculator()
        self.explain_builder = BehaviourExplainBuilder()
        self._cache: Dict[str, EngineResult] = {}
    
    def run(self, device_id: str, timeline: Timeline) -> EngineResult:
        """
        Главный метод движка.
        
        Args:
            device_id: Идентификатор устройства
            timeline: Timeline устройства (от TimelineBuilder)
        
        Returns:
            EngineResult: Результат работы движка
        """
        start_time = time.time()
        
        # === 1. Проверка кэша ===
        cache_key = self._get_cache_key(device_id)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cached.statistics.computation_time_ms = 0.0  # Кэш мгновенный
            return cached
        
        stats = EngineStatistics()
        
        # === 2. Metrics (из Metric Registry) ===
        metrics = MetricRegistry.build(timeline)
        stats.metrics_computed = len(metrics)
        
        # === 3. Features (из Feature Registry) ===
        features = FeatureRegistry.build(metrics)
        stats.features_computed = len(features)
        
        # === 4. Rules (из Rule Registry) ===
        rules = RuleRegistry.get_by_engine("behaviour")
        stats.rules_evaluated = len(rules)
        
        # === 5. Facts (через Fact Builder) ===
        facts = self.facts_builder.build({"features": features})
        stats.facts_generated = len(facts)
        stats.rules_matched = len(set(f.matched_rules[0] for f in facts if f.matched_rules))
        stats.rules_skipped = stats.rules_evaluated - stats.rules_matched
        
        # === 6. Coverage ===
        coverage = self.coverage_calculator.calculate(
            metrics=metrics,
            features=features,
            rules_evaluated=stats.rules_evaluated,
            rules_matched=stats.rules_matched,
            facts_count=stats.facts_generated
        )
        
        # === 7. Explain ===
        explain = self.explain_builder.build_explain(facts, metrics, features)
        
        # === 8. Debug ===
        debug = {
            "metrics": list(metrics.keys()),
            "features": list(features.keys()),
            "rules_evaluated": stats.rules_evaluated,
            "rules_matched": stats.rules_matched,
            "timeline_events": len(timeline.events)
        }
        
        # === 9. Version Snapshot ===
        version_snapshot = VersionSnapshot(
            metric="1.0.0",
            feature="1.0.0",
            rule="1.0.0",
            engine="1.0.0"
        )
        
        # === 10. Engine Result ===
        result = EngineResult(
            device_id=device_id,
            engine="behaviour",
            facts=facts,
            coverage=coverage,
            statistics=stats,
            debug=debug,
            version="1.0.0",
            explain=explain,
            generated_at=datetime.now(),
            version_snapshot=version_snapshot
        )
        
        # Сохраняем в кэш
        self._cache[cache_key] = result
        
        stats.computation_time_ms = (time.time() - start_time) * 1000
        result.statistics = stats
        
        return result
    
    def _get_cache_key(self, device_id: str) -> str:
        """Формирует ключ кэша на основе VersionSnapshot."""
        snapshot = VersionSnapshot(
            metric="1.0.0",
            feature="1.0.0",
            rule="1.0.0",
            engine="1.0.0"
        )
        return f"{device_id}:{snapshot.to_cache_key()}"
