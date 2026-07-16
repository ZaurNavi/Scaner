#!/usr/bin/env python3
"""Platform — центр управления всеми движками."""
from typing import Dict, List
from .platform_context import PlatformContext
from .bundles import MetricBundle, FeatureBundle, RuleBundle
from .base_engine import BaseEngine, EngineResult
from ..timeline.models import Timeline
from ..timeline.builder import TimelineBuilder
from ..registry.metric_registry import MetricRegistry
from ..registry.feature_registry import FeatureRegistry
from ..registry.rule_registry import RuleRegistry

class Platform:
    """
    Platform Core — управляет всеми движками.
    
    Platform.start() регистрирует все движки.
    Platform.run(device_id) выполняет полный pipeline.
    """
    
    _engines: Dict[str, BaseEngine] = {}
    _timeline_builder: TimelineBuilder = None
    
    @classmethod
    def start(cls):
        """Запускает Platform и регистрирует все движки."""
        print("  [PLATFORM] Starting Scanner Platform Core...")
        
        # Инициализируем Timeline Builder
        cls._timeline_builder = TimelineBuilder()
        
        # Регистрируем движки
        from ..behaviour.engine import BehaviourEngine
        cls.register_engine("behaviour", BehaviourEngine())
        
        print("  [PLATFORM] ✅ All engines registered")
    
    @classmethod
    def register_engine(cls, name: str, engine: BaseEngine):
        """Регистрирует движок."""
        cls._engines[name] = engine
    
    @classmethod
    def run(cls, device_id: str) -> Dict[str, EngineResult]:
        """
        Выполняет полный pipeline для устройства.
        
        Returns:
            Dict[str, EngineResult]: Результаты всех движков
        """
        results = {}
        
        # === 1. Timeline ===
        timeline = cls._timeline_builder.build(device_id)
        
        # === 2. Metrics (Platform вычисляет) ===
        metrics_dict = MetricRegistry.build(timeline)
        metric_bundle = MetricBundle(metrics=metrics_dict)
        
        # === 3. Features (Platform вычисляет) ===
        features_dict = FeatureRegistry.build(metrics_dict)
        feature_bundle = FeatureBundle(features=features_dict)
        
        # === 4. Rules (Platform предоставляет) ===
        rule_bundle = RuleBundle(rules=list(RuleRegistry.get_all().values()))
        
        # === 5. PlatformContext ===
        context = PlatformContext(
            device_id=device_id,
            timeline=timeline,
            metrics=metric_bundle,
            features=feature_bundle,
            rules=rule_bundle
        )
        
        # === 6. Запуск всех движков ===
        for engine_name, engine in cls._engines.items():
            try:
                result = engine.run(context)
                results[engine_name] = result
            except Exception as e:
                print(f"  [PLATFORM] ❌ Engine {engine_name} failed: {e}")
        
        return results
