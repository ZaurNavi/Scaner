#!/usr/bin/env python3
"""Platform — центр управления всеми движками."""
from typing import Dict, List, Optional, Any
from .platform_context import PlatformContext
from .bundles import MetricBundle, FeatureBundle, RuleBundle
from .base_engine import BaseEngine, EngineResult
from ..builders.timeline_builder import TimelineBuilder
from ..registry.metric_registry import MetricRegistry
from ..registry.feature_registry import FeatureRegistry
from ..registry.rule_registry import RuleRegistry

# v1.6.9.2: Configuration Layer Integration
from configuration import ConfigurationManager, get_config_manager


class Platform:
    """
    Platform Core — управляет всеми движками.
    
    v1.6.9.2: Platform принимает ConfigurationManager через конструктор.
    Движки регистрируются вручную через register_engine().
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        v1.6.9.2: Конструктор принимает ConfigurationManager через DI.
        """
        self.configuration = configuration
        self._engines: Dict[str, BaseEngine] = {}
        self._timeline_builder: TimelineBuilder = None
        self._started: bool = False
    
    def start(self):
        """
        Запускает Platform.
        
        v1.6.9.2: Инициализирует Timeline Builder.
        Движки НЕ регистрируются автоматически — используйте register_engine().
        """
        if self._started:
            print("  [PLATFORM] ⚠️  Platform already started, skipping")
            return
        
        print("  [PLATFORM] Starting Scanner Platform Core...")
        
        # Инициализируем Timeline Builder
        self._timeline_builder = TimelineBuilder()
        
        # v1.6.9.2: Движки НЕ регистрируются здесь автоматически.
        # Они должны быть зарегистрированы вручную через register_engine().
        
        self._started = True
        print("  [PLATFORM] ✅ Platform Core initialized")
    
    def register_engine(self, name: str, engine: BaseEngine):
        """Регистрирует движок."""
        self._engines[name] = engine
    
    def run(self, device_id: str) -> Dict[str, EngineResult]:
        """
        Выполняет полный pipeline для устройства.
        
        Returns:
            Dict[str, EngineResult]: Результаты всех движков
        """
        results = {}
        
        # === 1. Timeline ===
        timeline = self._timeline_builder.build(device_id)
        
        # === 2. Metrics ===
        metrics_dict = MetricRegistry.build(timeline)
        metric_bundle = MetricBundle(metrics=metrics_dict)
        
        # === 3. Features ===
        features_dict = FeatureRegistry.build(metrics_dict)
        feature_bundle = FeatureBundle(features=features_dict)
        
        # === 4. Rules ===
        rule_bundle = RuleBundle(rules=list(RuleRegistry.get_all().values()))
        
        # === 5. PlatformContext (с configuration) ===
        context = PlatformContext(
            device_id=device_id,
            timeline=timeline,
            metrics=metric_bundle,
            features=feature_bundle,
            rules=rule_bundle,
            configuration=self.configuration  # v1.6.9.2: DI
        )
        
        # === 6. Запуск всех движков ===
        for engine_name, engine in self._engines.items():
            try:
                result = engine.run(context)
                results[engine_name] = result
            except Exception as e:
                print(f"  [PLATFORM] ❌ Engine {engine_name} failed: {e}")
        
        return results
    
    def get_config_value(self, param_id: str, default=None):
        """Шорткат для получения значения параметра."""
        try:
            return self.configuration.get(param_id)
        except Exception:
            return default
