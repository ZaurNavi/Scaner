#!/usr/bin/env python3
"""Ядро Mobility Engine. Тонкий оркестратор."""
import time
from typing import Dict, Tuple
from datetime import datetime

from .models import MobilityProfile, MobilityFeatureSet, MobilityTimeline, DebugInfo, MovementEvent
from .evaluator import MobilityEvaluator
from .registry import ProviderRegistry, FeatureRegistry
from .constants import ENGINE_VERSION, RULES_VERSION

class MobilityEngine:
    def __init__(self, identity_service, session_engine, history_service):
        self.identity_service = identity_service
        self.session_engine = session_engine
        self.history_service = history_service
        self.evaluator = MobilityEvaluator()
        self._cache: Dict[Tuple, MobilityProfile] = {}

    def _get_versions(self, device_id: str) -> Tuple[str, int, int, int, int]:
        # Получаем реальные версии напрямую от identity_service
        id_ver = getattr(self.identity_service, 'get_version', lambda x: 1)(device_id)
        sess_ver = 1
        hist_ver = 1
        mob_ver = 1
        return (device_id, id_ver, mob_ver, sess_ver, hist_ver)

    def analyze(self, device_id: str) -> Tuple[MobilityProfile, DebugInfo]:
        start_time = time.time()
        debug = DebugInfo(computation_time_ms=0)
        
        # 1. Проверка кэша по составному ключу
        cache_key = self._get_versions(device_id)
        if cache_key in self._cache:
            debug.cache_invalidated = False
            debug.computation_time_ms = (time.time() - start_time) * 1000
            return self._cache[cache_key], debug

        debug.cache_invalidated = True
        debug.cache_reason = "Version mismatch or cold cache"

        # 2. Provider Manager
        metrics = {}
        providers = ProviderRegistry.get_all()
        for name, provider_cls in providers.items():
            t0 = time.time()
            if name == "session_provider":
                metrics.update(provider_cls(self.session_engine).extract(device_id))
            debug.provider_times[name] = (time.time() - t0) * 1000

        # 3. Feature Builder
        feature_set: MobilityFeatureSet = {}
        feature_builders = FeatureRegistry.get_all()
        for feat_id, builder in feature_builders.items():
            t0 = time.time()
            try:
                feature = builder(metrics)
                feature_set[feat_id] = feature
                if not feature.availability.available:
                    debug.missing_features.append(feat_id)
            except Exception:
                debug.missing_features.append(feat_id)
            debug.feature_times[feat_id] = (time.time() - t0) * 1000

        # 4. Evaluator
        facts, eval_debug = self.evaluator.evaluate(feature_set, metrics)
        debug.evaluated_rules = eval_debug["evaluated"]
        debug.matched_rules = eval_debug["matched"]
        debug.skipped_rules = eval_debug["skipped"]

        # 5. Profile Builder & Correct Coverage
        available_count = sum(1 for f in feature_set.values() if f.availability.available)
        supported_count = len(feature_builders)
        feature_coverage = (available_count / supported_count * 100) if supported_count > 0 else 0.0
        
        matched_rules_count = len(debug.matched_rules)
        enabled_rules_count = len([r for r in eval_debug["all_rules"] if r.enabled])
        mobility_coverage = (matched_rules_count / enabled_rules_count * 100) if enabled_rules_count > 0 else 0.0

        profile = MobilityProfile(
            identity_id=device_id,
            engine_version=ENGINE_VERSION,
            rules_version=RULES_VERSION,
            identity_version=cache_key[1], behaviour_version=cache_key[2],
            session_version=cache_key[3], history_version=cache_key[4],
            feature_coverage=feature_coverage,
            mobility_coverage=mobility_coverage,
            features=feature_set,
            facts=facts,
            timeline=MobilityTimeline(events=[MovementEvent(datetime.now(), None, "AP-1", "initial", -50, 0.9)])
        )

        self._cache[cache_key] = profile
        debug.computation_time_ms = (time.time() - start_time) * 1000
        return profile, debug
