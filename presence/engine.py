#!/usr/bin/env python3
"""Ядро Presence Engine с ProviderManager в конструкторе (Замечание №2, №11, №12)."""
import time
from typing import Dict, Tuple, Any
from datetime import datetime

from .models import PresenceProfile, PresenceFeatureSet, Timeline, DebugInfo
from .evaluator import PresenceEvaluator
from .timeline import TimelineFactory
from .builders.metrics_builder import MetricsBuilder
from .registry import ProviderRegistry, FeatureRegistry
from .constants import ENGINE_VERSION, RULES_VERSION, FEATURE_VERSION, PROVIDER_VERSION

# VersionProvider (Замечание №11)
class VersionProvider:
    """Получает версии сервисов для кэширования."""
    
    @staticmethod
    def get_history_version(identity_id: str) -> int:
        return 1  # Заглушка
    
    @staticmethod
    def get_session_version(identity_id: str) -> int:
        return 1  # Заглушка
    
    @staticmethod
    def get_presence_version(identity_id: str) -> int:
        return 1  # Заглушка

class ProviderManager:  # Замечание №2: вынесен в конструктор
    """Управляет всеми провайдерами. Engine не знает о конкретных реализациях."""
    
    def __init__(self):
        self._providers = {}
    
    def register(self, name: str, provider_instance):
        self._providers[name] = provider_instance
    
    def execute_all(self, device_id: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Выполняет все провайдеры и возвращает сырые данные + тайминги."""
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

class PresenceEngine:
    def __init__(self, history_service):
        self.history_service = history_service
        self.evaluator = PresenceEvaluator()
        self.timeline_factory = TimelineFactory()
        self.metrics_builder = MetricsBuilder()
        self.provider_manager = ProviderManager()  # Замечание №2
        self._cache: Dict[Tuple, PresenceProfile] = {}

    def _get_versions(self, device_id: str) -> Tuple[str, int, int, int]:
        # Замечение №11: VersionProvider
        history_ver = VersionProvider.get_history_version(device_id)
        session_ver = VersionProvider.get_session_version(device_id)
        presence_ver = VersionProvider.get_presence_version(device_id)
        return (device_id, history_ver, session_ver, presence_ver)

    def analyze(self, device_id: str) -> Tuple[PresenceProfile, DebugInfo]:
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

        # 1. Provider Manager (Замечание №2)
        raw_data, provider_times = self.provider_manager.execute_all(device_id)
        debug.provider_times = provider_times

        # 2. Metrics Builder
        t0 = time.time()
        metrics_set = self.metrics_builder.build(raw_data)
        debug.builder_times["metrics_builder"] = (time.time() - t0) * 1000

        # 3. Timeline Factory
        t0 = time.time()
        timeline = self.timeline_factory.build(raw_data)
        debug.builder_times["timeline_factory"] = (time.time() - t0) * 1000

        # 4. Feature Builder (Замечение №11 — автоматическая итерация)
        feature_set: PresenceFeatureSet = {}
        for feat_id, builder in FeatureRegistry.iterate():
            t0 = time.time()
            try:
                feature = builder(metrics_set)
                feature_set[feat_id] = feature
                if not feature.availability.available:
                    debug.missing_features.append(feat_id)
            except Exception:
                debug.missing_features.append(feat_id)
            debug.feature_times[feat_id] = (time.time() - t0) * 1000

        # 5. Evaluator
        facts, eval_debug = self.evaluator.evaluate(feature_set)
        debug.evaluated_rules = eval_debug["evaluated"]
        debug.matched_rules = eval_debug["matched"]
        debug.skipped_rules = eval_debug["skipped"]

        # 6. Coverage
        available_metrics = sum(1 for m in metrics_set.values() if m.availability.available)
        total_metrics = len(metrics_set.metrics)
        metric_coverage = (available_metrics / total_metrics * 100) if total_metrics > 0 else 0.0
        
        computed_features = sum(1 for f in feature_set.values() if f.availability.available)
        supported_features = len(feature_set)
        feature_coverage = (computed_features / supported_features * 100) if supported_features > 0 else 0.0
        
        matched_rules_count = len(debug.matched_rules)
        enabled_rules_count = len([r for r in eval_debug["all_rules"] if r.enabled])
        rule_match_ratio = (matched_rules_count / enabled_rules_count * 100) if enabled_rules_count > 0 else 0.0  # Замечение №5

        profile = PresenceProfile(
            identity_id=device_id,
            engine_version=ENGINE_VERSION,
            rules_version=RULES_VERSION,
            feature_version=FEATURE_VERSION,
            provider_version=PROVIDER_VERSION,
            history_version=cache_key[1],
            session_version=cache_key[2],
            presence_version=cache_key[3],
            metric_coverage=metric_coverage,
            feature_coverage=feature_coverage,
            rule_match_ratio=rule_match_ratio,  # Замечение №5
            timeline=timeline,
            metrics=metrics_set,  # Замечение №1: PresenceMetricSet
            features=feature_set,
            facts=facts
        )

        self._cache[cache_key] = profile
        debug.computation_time_ms = (time.time() - start_time) * 1000
        return profile, debug
