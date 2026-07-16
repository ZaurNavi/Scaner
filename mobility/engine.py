#!/usr/bin/env python3
"""Ядро Mobility Engine. Оркестрация конвейера."""
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .models import MobilityProfile, MobilityFeatureSet, MobilityTimeline, DebugInfo
from .evaluator import MobilityEvaluator
from .registry import ProviderRegistry, FeatureRegistry
from .constants import ENGINE_VERSION, RULES_VERSION

class MobilityEngine:
    def __init__(self, behaviour_service, session_engine, history_service):
        self.behaviour_service = behaviour_service
        self.session_engine = session_engine
        self.history_service = history_service
        self.evaluator = MobilityEvaluator()
        self._cache: Dict[str, MobilityProfile] = {}
        self._versions: Dict[str, Dict[str, int]] = {}

    def _check_cache(self, device_id: str, identity_version: int, behaviour_version: int) -> bool:
        if device_id not in self._cache:
            return False
        v = self._versions.get(device_id, {})
        return v.get("identity") == identity_version and v.get("behaviour") == behaviour_version

    def analyze(self, device_id: str) -> tuple[MobilityProfile, DebugInfo]:
        start_time = time.time()
        debug = DebugInfo(
            computation_time_ms=0, used_providers=[], skipped_rules=[], 
            missing_features=[], cache_invalidated=False, cache_reason=""
        )

        # 1. Получаем версии для кэша (упрощенно)
        identity_version = 1 # В реальности брать из IdentityService
        behaviour_version = 1 # В реальности брать из BehaviourService
        
        if self._check_cache(device_id, identity_version, behaviour_version):
            debug.cache_invalidated = False
            debug.computation_time_ms = (time.time() - start_time) * 1000
            return self._cache[device_id], debug

        debug.cache_invalidated = True
        debug.cache_reason = "Version mismatch or cold cache"

        # 2. Сбор Metrics через Providers
        metrics = {}
        providers = ProviderRegistry.get_all()
        for name, provider_cls in providers.items():
            # Инициализация провайдера (упрощенно)
            if name == "session_provider":
                provider = provider_cls(self.session_engine)
                metrics.update(provider.extract(device_id))
                debug.used_providers.append(name)

        # 3. Построение FeatureSet
        feature_set: MobilityFeatureSet = {}
        feature_builders = FeatureRegistry.get_all()
        
        for feat_id, builder in feature_builders.items():
            try:
                # Проверка зависимостей
                # (В полной версии здесь рекурсивная проверка availability)
                feature = builder(metrics)
                if feature.availability.available:
                    feature_set[feat_id] = feature
                else:
                    debug.missing_features.append(feat_id)
            except Exception:
                debug.missing_features.append(feat_id)

        # 4. Вычисление Timeline (заглушка для примера)
        timeline = MobilityTimeline()

        # 5. Evaluator
        facts = self.evaluator.evaluate(feature_set, timeline)

        # 6. Формирование Profile
        coverage = (len(feature_set) / len(feature_builders)) * 100 if feature_builders else 0
        profile = MobilityProfile(
            identity_id=device_id,
            engine_version=ENGINE_VERSION,
            rules_version=RULES_VERSION,
            identity_version=identity_version,
            behaviour_version=behaviour_version,
            feature_coverage=coverage,
            mobility_coverage=(len(facts) / len(facts)) * 100 if facts else 0, # Упрощено
            features=feature_set,
            facts=facts,
            timeline=timeline
        )

        # 7. Кэширование
        self._cache[device_id] = profile
        self._versions[device_id] = {"identity": identity_version, "behaviour": behaviour_version}

        debug.computation_time_ms = (time.time() - start_time) * 1000
        return profile, debug
