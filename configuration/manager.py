#!/usr/bin/env python3
"""ConfigurationManager - главный публичный API Configuration Layer."""
import time
from typing import Dict, Any, Optional
from .registry import ConfigRegistry
from .repository import ConfigRepository
from .validator import ConfigValidator
from .defaults import register_defaults
from .exceptions import ConfigFrozenError, ConfigUnknownParameterError, ConfigValidationError

class ConfigurationManager:
    """
    Singleton менеджер конфигурации.
    Обеспечивает загрузку, валидацию, freeze и O(1) доступ.
    """
    _instance: Optional['ConfigurationManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._repository = ConfigRepository()
        self._is_frozen = False
        self._cache: Dict[str, Any] = {}
        self._initialized = True
        
        # Регистрируем параметры по умолчанию
        register_defaults()
    
    def load(self, source: Dict[str, Any]) -> None:
        """Загружает и валидирует конфигурацию из словаря."""
        if self._is_frozen:
            raise ConfigFrozenError("Configuration is frozen and cannot be loaded again")
        
        self._repository.clear()
        self._cache.clear()
        
        start_time = time.time()
        
        # 1. Заполняем значениями по умолчанию
        for param_id, param in ConfigRegistry.get_all().items():
            self._repository.set(param_id, param.default)
            
        # 2. Перезаписываем пользовательскими значениями с валидацией
        for param_id, value in source.items():
            if param_id not in ConfigRegistry.get_all():
                raise ConfigUnknownParameterError(f"Unknown parameter in source: {param_id}")
            
            param = ConfigRegistry.get(param_id)
            validated_value = ConfigValidator.validate(param, value)
            self._repository.set(param_id, validated_value)
            
        # 3. Строим кэш для O(1) доступа
        self._cache = self._repository.get_all()
        
        load_time_ms = (time.time() - start_time) * 1000
        if load_time_ms > 100:
            # Предупреждение в лог, но не ошибка, т.к. 100мс - мягкое требование
            pass 

    def freeze(self) -> None:
        """Делает конфигурацию иммутабельной."""
        self._is_frozen = True
        
    def get(self, param_id: str) -> Any:
        """Получает значение параметра. O(1)."""
        if param_id not in self._cache:
            raise ConfigUnknownParameterError(f"Unknown parameter: {param_id}")
        return self._cache[param_id]
    
    def exists(self, param_id: str) -> bool:
        """Проверяет существование параметра."""
        return param_id in ConfigRegistry.get_all()
    
    def group(self, group_name: str) -> Dict[str, Any]:
        """Получает все параметры группы как словарь."""
        group_params = ConfigRegistry.get_group(group_name)
        return {
            param_id: self._cache[param_id] 
            for param_id in group_params.keys()
        }
    
    def dump(self) -> Dict[str, Any]:
        """Возвращает полную текущую конфигурацию как словарь."""
        return self._cache.copy()
    
    def export(self) -> Dict[str, Any]:
        """Экспортирует конфигурацию с метаданными (для UI/Debug)."""
        result = {}
        for param_id, param in ConfigRegistry.get_all().items():
            result[param_id] = {
                "value": self._cache[param_id],
                "type": param.type.__name__,
                "group": param.group,
                "description": param.description,
                "mutable": param.mutable,
                "deprecated": param.deprecated
            }
        return result

    def validate(self) -> bool:
        """Проверяет текущую конфигурацию. Вызывает исключение при ошибке."""
        for param_id, param in ConfigRegistry.get_all().items():
            value = self._cache.get(param_id)
            ConfigValidator.validate(param, value)
        return True

# Глобальный доступ (для DI можно передавать экземпляр этого класса)
def get_config_manager() -> ConfigurationManager:
    return ConfigurationManager()
