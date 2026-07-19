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

# v1.6.9.1: Configuration Layer Integration
from configuration import ConfigurationManager, get_config_manager


class Platform:
    """
    Platform Core — управляет всеми движками.
    
    Platform.start() регистрирует все движки и инициализирует ConfigurationManager.
    Platform.run(device_id) выполняет полный pipeline.
    Platform.get_configuration() предоставляет доступ к ConfigurationManager.
    Platform.get_config_value(param_id, default) — шорткат для получения значения.
    """
    
    _engines: Dict[str, BaseEngine] = {}
    _timeline_builder: TimelineBuilder = None
    
    # v1.6.9.1: ConfigurationManager — единый источник конфигурации
    _configuration_manager: Optional[ConfigurationManager] = None
    
    # v1.6.9.1: Флаг защиты от повторного запуска
    _started: bool = False
    
    @classmethod
    def start(cls):
        """
        Запускает Platform и регистрирует все движки.
        
        v1.6.9.1: Также инициализирует ConfigurationManager (один раз).
        Защищён от повторного вызова.
        """
        # Защита от повторного вызова
        if cls._started:
            print("  [PLATFORM] ⚠️  Platform already started, skipping")
            return
        
        print("  [PLATFORM] Starting Scanner Platform Core...")
        
        # v1.6.9.1: Инициализация ConfigurationManager (только один раз)
        cls._initialize_configuration()
        
        # Инициализируем Timeline Builder
        cls._timeline_builder = TimelineBuilder()
        
        # Регистрируем движки
        from ..behaviour.engine import BehaviourEngine
        cls.register_engine("behaviour", BehaviourEngine())
        
        # Устанавливаем флаг
        cls._started = True
        
        print("  [PLATFORM] ✅ All engines registered")
    
    @classmethod
    def _initialize_configuration(cls):
        """
        v1.6.9.1: Инициализирует ConfigurationManager (один раз).
        
        ConfigurationManager — Singleton. Если он уже существует и заморожен
        (например, инициализирован в monitor.py), просто используем его.
        Иначе — создаём, загружаем, валидируем и замораживаем.
        """
        if cls._configuration_manager is not None:
            # Уже инициализирован в Platform — пропускаем
            return
        
        # Получаем существующий Singleton экземпляр
        cls._configuration_manager = get_config_manager()
        
        # v1.6.9.1a: Используем публичный метод is_frozen() вместо приватного поля
        if cls._configuration_manager.is_frozen():
            # ConfigurationManager уже инициализирован где-то раньше (например, в monitor.py)
            # Просто используем его — не пытаемся перезагрузить
            print("  [PLATFORM] ✅ ConfigurationManager already initialized (reusing existing)")
            return
        
        # ConfigurationManager ещё не заморожен — инициализируем его
        cls._configuration_manager.load({})
        cls._configuration_manager.validate()
        cls._configuration_manager.freeze()
        
        print("  [PLATFORM] ✅ ConfigurationManager initialized and frozen")
    
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
    
    @classmethod
    def get_configuration(cls) -> ConfigurationManager:
        """
        v1.6.9.1: Предоставляет публичный доступ к ConfigurationManager.
        
        Все остальные модули будут получать настройки через этот метод.
        
        Ленивая инициализация: Если ConfigurationManager ещё не инициализирован,
        метод автоматически вызовет _initialize_configuration(). Это позволяет
        использовать Platform.get_configuration() даже если Platform.start()
        ещё не был вызван (например, в тестах или при раннем доступе к конфигурации).
        
        Returns:
            ConfigurationManager: Единый источник конфигурации платформы
        
        Пример:
            config = Platform.get_configuration()
            scan_interval = config.get("monitor.scan_interval")
        """
        # Ленивая инициализация: если ConfigurationManager ещё не создан
        if cls._configuration_manager is None:
            cls._initialize_configuration()
        
        return cls._configuration_manager
    
    @classmethod
    def get_config_value(cls, param_id: str, default: Any = None) -> Any:
        """
        v1.6.9.1: Шорткат для получения значения параметра.
        
        Удобный метод, чтобы не тянуть весь ConfigurationManager везде.
        
        v1.6.9.1a: Добавлен параметр default для обработки отсутствующих параметров.
        
        Args:
            param_id: Идентификатор параметра (например, "monitor.scan_interval")
            default: Значение по умолчанию, если параметр не найден (по умолчанию None)
        
        Returns:
            Any: Значение параметра или default, если параметр не существует
        
        Пример:
            interval = Platform.get_config_value("monitor.scan_interval")
            timeout = Platform.get_config_value("custom.timeout", default=30)
        """
        try:
            return cls.get_configuration().get(param_id)
        except Exception:
            # v1.6.9.1a: Возвращаем default при отсутствии параметра
            return default
