#!/usr/bin/env python3
"""ConfigurationManager - главный публичный API Configuration Layer."""
import time
from types import MappingProxyType
from typing import Dict, Any, Optional
from .registry import ConfigRegistry
from .repository import ConfigRepository
from .validator import ConfigValidator
from .loader import ConfigLoader
from .serializer import ConfigSerializer
from .exceptions import ConfigFrozenError, ConfigUnknownParameterError, ConfigValidationError

class ConfigurationManager:
    """
    Singleton менеджер конфигурации.
    Обеспечивает загрузку, валидацию, freeze и O(1) доступ.
    Registry приватен — доступ только через Manager.
    """
    _instance: Optional['ConfigurationManager'] = None
    _registry: Optional[ConfigRegistry] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Приватный Registry — доступ только через Manager
        ConfigurationManager._registry = ConfigRegistry()
        self._repository = ConfigRepository()
        self._is_frozen = False
        self._cache: Dict[str, Any] = {}
        self._defaults_registered = False
        self._initialized = True
    
    def _register_defaults(self):
        """Регистрирует параметры по умолчанию (вызывается один раз)."""
        if self._defaults_registered:
            return
        
        from .defaults import register_defaults
        register_defaults(self._registry)
        self._defaults_registered = True
    
    def load(self, source: Dict[str, Any] = None) -> None:
        """Загружает и валидирует конфигурацию из словаря."""
        if self._is_frozen:
            raise ConfigFrozenError("Configuration is frozen and cannot be loaded again")
        
        if source is None:
            source = {}
        
        self._repository.clear()
        # ИСПРАВЛЕНО: пересоздаём _cache вместо clear() (MappingProxyType не имеет clear)
        self._cache = {}
        
        # Регистрируем defaults при первой загрузке
        self._register_defaults()
        
        start_time = time.time()
        
        # 1. Заполняем значениями по умолчанию
        for param_id, param in self._registry.get_all().items():
            self._repository.set(param_id, param.default)
            
        # 2. Перезаписываем пользовательскими значениями с валидацией
        for param_id, value in source.items():
            if param_id not in self._registry.get_all():
                raise ConfigUnknownParameterError(f"Unknown parameter in source: {param_id}")
            
            param = self._registry.get(param_id)
            validated_value = ConfigValidator.validate(param, value)
            self._repository.set(param_id, validated_value)
            
        # 3. Строим кэш для O(1) доступа
        self._cache = self._repository.get_all()
        
        load_time_ms = (time.time() - start_time) * 1000
        if load_time_ms > 100:
            pass  # Предупреждение в лог

    def load_from_json(self, file_path: str) -> None:
        """Загружает конфигурацию из JSON файла."""
        data = ConfigLoader.from_json(file_path)
        self.load(data)
    
    def load_from_env(self, prefix: str = "SCANNER_") -> None:
        """Загружает конфигурацию из переменных окружения."""
        data = ConfigLoader.from_env(prefix)
        self.load(data)
    
    def reload(self, source: Dict[str, Any] = None) -> None:
        """Перезагружает конфигурацию (снимает freeze, если был)."""
        self._is_frozen = False
        self.load(source)
    
    def freeze(self) -> None:
        """Делает конфигурацию иммутабельной."""
        # Преобразуем кэш в MappingProxyType для защиты от изменений
        self._cache = MappingProxyType(self._cache)
        self._is_frozen = True
        
    def get(self, param_id: str) -> Any:
        """Получает значение параметра. O(1)."""
        if param_id not in self._cache:
            raise ConfigUnknownParameterError(f"Unknown parameter: {param_id}")
        return self._cache[param_id]
    
    def exists(self, param_id: str) -> bool:
        """Проверяет существование параметра."""
        return param_id in self._registry.get_all()
    
    def group(self, group_name: str) -> Dict[str, Any]:
        """Получает все параметры группы как словарь."""
        group_params = self._registry.get_group(group_name)
        return {
            param_id: self._cache[param_id] 
            for param_id in group_params.keys()
        }
    
    def dump(self) -> Dict[str, Any]:
        """Возвращает полную текущую конфигурацию как словарь."""
        return dict(self._cache)
    
    def export(self) -> Dict[str, Any]:
        """Экспортирует конфигурацию с метаданными (для UI/Debug)."""
        result = {}
        for param_id, param in self._registry.get_all().items():
            result[param_id] = {
                "value": self._cache[param_id],
                "type": param.type.__name__,
                "group": param.group,
                "description": param.description,
                "mutable": param.mutable,
                "deprecated": param.deprecated,
                "required": param.required
            }
        return result

    def validate(self) -> bool:
        """Проверяет текущую конфигурацию. Вызывает исключение при ошибке."""
        for param_id, param in self._registry.get_all().items():
            value = self._cache.get(param_id)
            ConfigValidator.validate(param, value)
        return True
    
    def save_to_json(self, file_path: str) -> None:
        """Сохраняет текущую конфигурацию в JSON файл."""
        ConfigSerializer.to_file(self.dump(), file_path)

# Глобальный доступ
def get_config_manager() -> ConfigurationManager:
    return ConfigurationManager()
