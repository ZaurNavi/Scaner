#!/usr/bin/env python3
"""Platform — центр управления всеми движками."""
from typing import Dict, List
from .platform_context import PlatformContext
from .bundles import MetricBundle, FeatureBundle, RuleBundle
from .base_engine import BaseEngine, EngineResult
from ..builders.timeline_builder import TimelineBuilder
from ..registry.metric_registry import MetricRegistry
from ..registry.feature_registry import FeatureRegistry
from ..registry.rule_registry import RuleRegistry

# v1.6.9.2: Configuration Layer Integration (Dependency Injection)
from configuration import ConfigurationManager


class Platform:
    """
    Platform Core — управляет всеми движками.
    
    v1.6.9.2: Platform принимает ConfigurationManager через конструктор.
    Никаких Singleton. Никаких classmethod. Полностью instance-based.
    
    Пример использования:
        config = ConfigurationManager()
        config.load({})
        config.freeze()
        
        platform = Platform(configuration=config)
        platform.start()
        results = platform.run(device_id)
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        v1.6.9.2: Конструктор принимает ConfigurationManager через DI.
        
        Args:
            configuration: Единый источник конфигурации платформы
        """
        self.configuration = configuration
        self._engines: Dict[str, BaseEngine] = {}
        self._timeline_builder: TimelineBuilder = None
        self._started: bool = False
    
    def start(self):
        """
        Запускает Platform и регистрирует все движки.
        
        v1.6.9.2: Instance method (не classmethod).
        Защищён от повторного вызова.
        """
        # Защита от повторного вызова
        if self._started:
            print("  [PLATFORM] ⚠️  Platform already started, skipping")
            return
        
        print("  [PLATFORM] Starting Scanner Platform Core...")
        
        # Инициализируем Timeline Builder
        self._timeline_builder = TimelineBuilder()
        
        # Регистрируем движки с передачей configuration
        from ..behaviour.engine import BehaviourEngine
        self.register_engine("behaviour", BehaviourEngine(
            engine_name="behaviour",
            engine_rules=list(RuleRegistry.get_by_engine("behaviour").values()),
            configuration=self.configuration  # v1.6.9.2: DI
        ))
        
        # Устанавливаем флаг
        self._started = True
        
        print("  [PLATFORM] ✅ All engines registered")
    
    def register_engine(self, name: str, engine: BaseEngine):
        """Регистрирует движок."""
        self._engines[name] = engine
    
    def run(self, device_id: str) -> Dict[str, EngineResult]:
        """
        Выполняет полный pipeline для устройства.
        
        v1.6.9.2: Instance method (не classmethod).
        
        Returns:
            Dict[str, EngineResult]: Результаты всех движков
        """
        results = {}
        
        # === 1. Timeline ===
        timeline = self._timeline_builder.build(device_id)
        
        # === 2. Metrics (Platform вычисляет) ===
        metrics_dict = MetricRegistry.build(timeline)
        metric_bundle = MetricBundle(metrics=metrics_dict)
        
        # === 3. Features (Platform вычисляет) ===
        features_dict = FeatureRegistry.build(metrics_dict)
        feature_bundle = FeatureBundle(features=features_dict)
        
        # === 4. Rules (Platform предоставляет) ===
        rule_bundle = RuleBundle(rules=list(RuleRegistry.get_all().values()))
        
        # === 5. PlatformContext (с configuration) ===
        context = PlatformContext(
            device_id=device_id,
            timeline=timeline,
            metrics=metric_bundle,
            features=feature_bundle,
            rules=rule_bundle,
            configuration=self.configuration  # v1.6.9.2: DI через Context
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
        """
        v1.6.9.2: Шорткат для получения значения параметра.
        
        Args:
            param_id: Идентификатор параметра
            default: Значение по умолчанию
        
        Returns:
            Значение параметра или default
        """
        try:
            return self.configuration.get(param_id)
        except Exception:
            return default
