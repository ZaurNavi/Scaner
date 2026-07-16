#!/usr/bin/env python3
"""Ядро Usage Engine (тонкий оркестратор)."""
import time
from typing import Dict, Tuple, Any
from datetime import datetime

from .models import UsageProfile, UsageFeatureSet, Timeline, DebugInfo, VersionSnapshot, UsageQuality
from .evaluator import UsageEvaluator
from .builders.timeline_builder import TimelineBuilder
from .builders.metrics_builder import MetricsBuilder
from .builders.feature_builder import FeatureBuilder
from .builders.fact_builder import FactBuilder
from .registry import ProviderRegistry
from .constants import ENGINE_VERSION, RULES_VERSION, FEATURE_VERSION, PROVIDER_VERSION, METRICS_VERSION, TIMELINE_VERSION

class ProviderManager:
    def __init__(self):
        self._providers = {}
    
    def register(self, name: str, provider_instance):
        self._providers[name] = provider_instance
    
    def execute_all(self, device_id: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        raw_data = {}
        timings = {}
        
        for name, provider in self._providers.items():
            t0 = time.time()
            try:
                data = provider.extract(device_id)
                raw_data.update(data)
            except Exception as e:
                raw_data[f"{name}_error"] = str(e)
            timings[name] = (time.time() - t0) * 1000
        
        return raw_data, timings

class UsageEngine:
    def __init__(self, history_service):
        self.history_service = history_service
        self.evaluator = UsageEvaluator()
        self.timeline_builder = TimelineBuilder()
        self.metrics_builder = MetricsBuilder()
        self.feature_builder = FeatureBuilder()
        self.fact_builder = FactBuilder()
        self.provider_manager = ProviderManager()
        self._cache: Dict[Tuple, UsageProfile] = {}

    def _get_versions(self, device_id: str) -> Tuple[str, int, int, int]:
        # Заглушка: в реальной системе версии берутся из сервисов
        identity_ver = 1
        history_ver = 1
        session_ver = 1
        usage_ver = 1
        return (device_id, identity_ver, history_ver, session_ver, usage_ver)

    def analyze(self, device_id: str) -> Tuple[UsageProfile, DebugInfo]:
        start_time = time.time()
        debug = DebugInfo(
            computation_time_ms=0,
            engine_version=ENGINE_VERSION,
            feature_version=FEATURE_VERSION,
            provider_version=PROVIDER_VERSION
        )
        
        cache_key = self._get_versions(device_id)
        debug.cache_key = cache_key
        
        if cache_key in self._cache:
            debug.cache_invalidated = False
            debug.cache_hit = True
            debug.computation_time_ms = (time.time() - start_time) * 1000
            return self._cache[cache_key], debug

        debug.cache_invalidated = True
        debug.cache_hit = False
        debug.cache_reason = "Version mismatch or cold cache"

        # 1. Provider Manager
        raw_data, provider_times = self.provider_manager.execute_all(device_id)
        debug.provider_times = provider_times

        # 2. Timeline Builder
        t0 = time.time()
        traffic_events = raw_data.get("traffic_events", [])
        provider_quality = raw_data.get("provider_quality")
        timeline = self.timeline_builder.build(traffic_events)
        debug.builder_times["timeline_builder"] = (time.time() - t0) * 1000

        # 3. Metrics Builder
        t0 = time.time()
        metrics_set = self.metrics_builder.build(timeline, provider_quality)
        debug.builder_times["metrics_builder"] = (time.time() - t0) * 1000

        # 4. Feature Builder
        t0 = time.time()
        feature_set = self.feature_builder.build(metrics_set)
        debug.builder_times["feature_builder"] = (time.time() - t0) * 1000

        # 5. Evaluator (возвращает dict, не DebugInfo)
        matched_rules, eval_debug = self.evaluator.evaluate(feature_set, metrics_set)
        debug.evaluated_rules = eval_debug["evaluated"]
        debug.matched_rules = eval_debug["matched"]
        debug.skipped_rules = eval_debug["skipped"]
        debug.all_rules = eval_debug["all_rules"]  # ДОБАВЛЕНО

        # 6. Fact Builder
        facts = []
        for match in matched_rules:
            rule = match["rule"]
            fact = self.fact_builder.build_fact(
                category=rule.category,
                rule_id=rule.id,
                rule_name=rule.name,
                matched_features=match["matched_features"],
                feature_values=match["feature_values"],
                metrics=metrics_set,
                features=feature_set,
                weight=rule.weight
            )
            facts.append(fact)

        # 7. Coverage & Quality
        available_metrics = sum(1 for m in metrics_set.values() if m.confidence > 0)
        total_metrics = len(metrics_set.metrics)
        metric_coverage = (available_metrics / total_metrics * 100) if total_metrics > 0 else 0.0
        
        computed_features = len(feature_set)
        feature_coverage = (computed_features / 6 * 100) if computed_features > 0 else 0.0  # 6 features
        
        matched_rules_count = len(debug.matched_rules)
        enabled_rules_count = len([r for r in debug.all_rules if r.enabled])
        rule_match_ratio = (matched_rules_count / enabled_rules_count * 100) if enabled_rules_count > 0 else 0.0
        
        quality = UsageQuality(
            coverage=metric_coverage / 100.0,
            freshness=provider_quality.freshness if provider_quality else 0.0,
            samples=len(traffic_events),
            timeline_depth=len(timeline.events),
            confidence=sum(f.confidence for f in facts) / max(len(facts), 1) / 100.0,
            provider_quality={"traffic_provider": provider_quality.coverage} if provider_quality else {},
            timeline_quality=len(timeline.events) / max(len(traffic_events), 1),
            feature_quality=computed_features / 6.0,
            rule_quality=rule_match_ratio / 100.0
        )

        version_snapshot = VersionSnapshot(
            identity_version=str(cache_key[1]),
            history_version=str(cache_key[2]),
            traffic_version=TIMELINE_VERSION,
            rules_version=RULES_VERSION,
            feature_version=FEATURE_VERSION,
            provider_version=PROVIDER_VERSION
        )

        profile = UsageProfile(
            identity_id=device_id,
            engine_version=ENGINE_VERSION,
            rules_version=RULES_VERSION,
            feature_version=FEATURE_VERSION,
            provider_version=PROVIDER_VERSION,
            metrics_version=METRICS_VERSION,
            timeline_version=TIMELINE_VERSION,
            identity_version=cache_key[1],
            history_version=cache_key[2],
            session_version=cache_key[3],
            metric_coverage=metric_coverage,
            feature_coverage=feature_coverage,
            rule_match_ratio=rule_match_ratio,
            timeline=timeline,
            metrics=metrics_set,
            features=feature_set,
            facts=facts,
            quality=quality,
            version_snapshot=version_snapshot
        )

        self._cache[cache_key] = profile
        debug.computation_time_ms = (time.time() - start_time) * 1000
        return profile, debug
