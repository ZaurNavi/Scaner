#!/usr/bin/env python3
"""BaseEngine — базовый класс для всех движков платформы."""
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from dataclasses import dataclass, field
import time

from .platform_context import PlatformContext
from .bundles import MetricBundle, FeatureBundle
from ..facts.models import Fact, FactStatus
from ..coverage.platform import Coverage
from ..cache.platform import VersionSnapshot
from ..rules.evaluator import RuleEvaluator

# v1.6.9.2: Configuration Layer Integration
from configuration import ConfigurationManager


@dataclass
class ExecutionInfo:
    """Информация о выполнении движка."""
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime = None
    duration_ms: float = 0.0
    cache_hit: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class EngineResult:
    """Единый результат работы любого движка."""
    
    def __init__(
        self,
        device_id: str,
        engine: str,
        facts: List[Fact],
        coverage: Coverage,
        statistics: dict,
        debug: dict,
        explain: dict,
        dependencies: dict,
        version: str = "1.0.0",
        execution: ExecutionInfo = None
    ):
        self.device_id = device_id
        self.engine = engine
        self.facts = facts
        self.coverage = coverage
        self.statistics = statistics
        self.debug = debug
        self.explain = explain
        self.dependencies = dependencies
        self.version = version
        self.generated_at = datetime.now()
        self.execution = execution or ExecutionInfo()
        self.version_snapshot = VersionSnapshot(
            timeline_version="1.0.0",
            metric_version="1.0.0",
            feature_version="1.0.0",
            rule_version="1.0.0",
            knowledge_version="1.0.0",
            profile_version="1.0.0",
            profile_model_version="1.0.0"
        )


class BaseEngine(ABC):
    """
    Базовый класс для всех движков.
    
    v1.6.9.2: Принимает ConfigurationManager через конструктор.
    """
    
    def __init__(self, engine_name: str, engine_rules: List, configuration: ConfigurationManager):
        self.engine_name = engine_name
        self.engine_rules = engine_rules
        self.configuration = configuration  # v1.6.9.2: Configuration через DI
        self.evaluator = RuleEvaluator()
        self._cache = {}
    
    def run(self, context: PlatformContext) -> EngineResult:
        """Главный метод. Движок НЕ переопределяет его."""
        start_time = time.time()
        execution = ExecutionInfo(started_at=datetime.now())
        
        # === 1. Проверка кэша ===
        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cached_stats = dict(cached.statistics)
            cached_stats["computation_time_ms"] = 0.0
            cached_stats["cache_hit"] = True
            
            execution.finished_at = datetime.now()
            execution.duration_ms = 0.0
            execution.cache_hit = True
            
            return EngineResult(
                device_id=cached.device_id,
                engine=cached.engine,
                facts=cached.facts,
                coverage=cached.coverage,
                statistics=cached_stats,
                debug=cached.debug,
                explain=cached.explain,
                dependencies=cached.dependencies,
                version=cached.version,
                execution=execution
            )
        
        # === 2. Оценка правил ===
        matched_rules = []
        for rule in self.engine_rules:
            try:
                if self.evaluator.evaluate(rule, context.features.features):
                    matched_rules.append(rule)
            except Exception as e:
                execution.warnings.append(f"Rule {rule.id} failed: {e}")
        
        # === 3. Построение Facts ===
        facts = self._build_facts(matched_rules, context)
        
        # === 4. Coverage ===
        coverage = self._calculate_coverage(context, matched_rules, facts)
        
        # === 5. Explain ===
        explain = self._build_explain(facts, context)
        
        # === 6. Statistics ===
        statistics = {
            "rules_evaluated": len(self.engine_rules),
            "rules_matched": len(matched_rules),
            "facts_generated": len(facts)
        }
        
        # === 7. Debug ===
        debug = {
            "features_count": len(context.features.features),
            "rules_count": len(self.engine_rules),
            "matched_rules": [r.id for r in matched_rules]
        }
        
        # === 8. Dependencies ===
        dependencies = {
            "timeline_version": context.timeline.generated_at.isoformat() if hasattr(context.timeline, 'generated_at') else "1.0.0",
            "metric_version": context.metrics.version,
            "feature_version": context.features.version,
            "rule_version": context.rules.version
        }
        
        # === 9. Execution Info ===
        execution.finished_at = datetime.now()
        execution.duration_ms = (time.time() - start_time) * 1000
        execution.cache_hit = False
        
        # === 10. Engine Result ===
        result = EngineResult(
            device_id=context.device_id,
            engine=self.engine_name,
            facts=facts,
            coverage=coverage,
            statistics=statistics,
            debug=debug,
            explain=explain,
            dependencies=dependencies,
            version="1.0.0",
            execution=execution
        )
        
        # Сохраняем в кэш
        self._cache[cache_key] = result
        
        return result
    
    def _build_facts(self, matched_rules: List, context: PlatformContext) -> List[Fact]:
        """Строит Facts из matched rules."""
        from uuid import uuid4
        
        facts = []
        for rule in matched_rules:
            matched_features = [c.feature for c in rule.expression]
            confidence = min(rule.weight + len(matched_features) * 5, 100.0)
            status = FactStatus.HIGH if confidence >= 60 else FactStatus.MEDIUM if confidence >= 40 else FactStatus.LOW
            
            fact = Fact(
                id=str(uuid4()),
                engine=self.engine_name,
                category=rule.category,
                status=status,
                confidence=confidence,
                quality=0.9,
                sources=[self.engine_name],
                matched_rules=[rule.id],
                matched_features=matched_features,
                explain={
                    "rule": {"id": rule.id, "name": rule.name, "weight": rule.weight},
                    "features": {f: context.features.get(f) for f in matched_features}
                }
            )
            facts.append(fact)
        
        return facts
    
    def _calculate_coverage(self, context: PlatformContext, matched_rules: List, facts: List) -> Coverage:
        """Вычисляет Coverage."""
        total_rules = len(self.engine_rules)
        rules_matched = len(matched_rules)
        facts_count = len(facts)
        
        rule_coverage = (rules_matched / total_rules * 100) if total_rules > 0 else 0.0
        fact_coverage = (facts_count / total_rules * 100) if total_rules > 0 else 0.0
        
        return Coverage(
            timeline_coverage=100.0,
            metric_coverage=100.0,
            feature_coverage=100.0,
            rule_coverage=rule_coverage,
            fact_coverage=fact_coverage
        )
    
    def _build_explain(self, facts: List[Fact], context: PlatformContext) -> dict:
        """Строит Explain Trace."""
        return {
            "engine": self.engine_name,
            "facts": [
                {
                    "fact_id": f.id,
                    "category": f.category,
                    "confidence": f.confidence,
                    "chain": {
                        "rule": f.matched_rules,
                        "features": f.matched_features,
                        "metrics": f.matched_features
                    }
                }
                for f in facts
            ]
        }
    
    def _get_cache_key(self, context: PlatformContext) -> str:
        """Формирует ключ кэша."""
        snapshot = VersionSnapshot(
            timeline_version="1.0.0",
            metric_version="1.0.0",
            feature_version="1.0.0",
            rule_version="1.0.0",
            knowledge_version="1.0.0",
            profile_version="1.0.0",
            profile_model_version="1.0.0"
        )
        return f"{context.device_id}:{snapshot.to_cache_key()}"
