#!/usr/bin/env python3
"""
Passive Registry — реестр дескрипторов Passive Collectors.
ES-1.8.0: Registry хранит ТОЛЬКО дескрипторы (SRP).
ES-1.8.2: Добавлен default_category — категория идёт из Descriptor.

Архитектура:
Registry → Descriptor → Factory → Collector
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Type

from configuration import ConfigurationManager


# ==============================================================================
# PassiveCollectorDescriptor — полные метаданные коллектора
# ==============================================================================

@dataclass(frozen=True)
class PassiveCollectorDescriptor:
    """
    Полные метаданные Passive Collector'а.
    
    ES-1.8.2: Добавлено поле default_category.
    Категория идёт из Descriptor, а не строится вручную в Pipeline.
    
    Обязательные поля:
    - id: уникальный идентификатор
    - name: человекочитаемое имя
    - version: версия коллектора
    - protocol: протокол (DNS, mDNS, LLMNR, NBNS и т.д.)
    - category: категория (passive)
    - priority: приоритет (меньше = раньше)
    - enabled_by_default: включён ли по умолчанию
    - capabilities: кортеж возможностей
    - collector_cls: ссылка на класс коллектора
    - default_category: категория для нормализации (ES-1.8.2)
    """
    id: str
    name: str
    version: str
    protocol: str
    category: str = "passive"
    priority: int = 100
    enabled_by_default: bool = True
    capabilities: tuple = ()
    collector_cls: Type = None
    default_category: str = "identity"  # ES-1.8.2: Категория для нормализации


# ==============================================================================
# PassiveRegistry — реестр дескрипторов
# ==============================================================================

class PassiveRegistry:
    """
    Реестр Passive Collectors.
    
    v1.8.0: Registry хранит ТОЛЬКО дескрипторы.
    Создание экземпляров — задача PassiveCollectorFactory.
    SRP: Registry отвечает только за регистрацию и поиск.
    """
    
    _descriptors: Dict[str, PassiveCollectorDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: PassiveCollectorDescriptor) -> None:
        """
        Регистрирует дескриптор Passive Collector в реестре.
        
        Args:
            descriptor: Метаданные коллектора
        
        Raises:
            ValueError: Если ID уже зарегистрирован (защита от затирания)
        """
        # v1.8.0: Проверка дубликатов ID
        if descriptor.id in cls._descriptors:
            existing = cls._descriptors[descriptor.id]
            raise ValueError(
                f"Passive Collector ID '{descriptor.id}' already registered "
                f"by '{existing.name}' v{existing.version}. "
                f"Cannot overwrite with '{descriptor.name}'."
            )
        
        cls._descriptors[descriptor.id] = descriptor
    
    @classmethod
    def get_descriptor(cls, collector_id: str) -> Optional[PassiveCollectorDescriptor]:
        """Получает дескриптор коллектора по ID."""
        return cls._descriptors.get(collector_id)
    
    @classmethod
    def get_all_descriptors(cls) -> Dict[str, PassiveCollectorDescriptor]:
        """Получает все дескрипторы."""
        return cls._descriptors.copy()
    
    @classmethod
    def get_sorted_descriptors(cls) -> List[PassiveCollectorDescriptor]:
        """Получает все дескрипторы, отсортированные по приоритету."""
        return sorted(
            cls._descriptors.values(),
            key=lambda d: d.priority
        )
    
    @classmethod
    def iter_enabled_descriptors(
        cls,
        configuration: ConfigurationManager
    ) -> Iterator[PassiveCollectorDescriptor]:
        """
        Итерирует только включённые дескрипторы.
        
        Args:
            configuration: ConfigurationManager для проверки enabled
        
        Yields:
            PassiveCollectorDescriptor
        """
        for descriptor in cls.get_sorted_descriptors():
            # Проверяем enabled_by_default из дескриптора
            # И опционально из Configuration Layer
            config_key = f"fingerprint.collectors.{descriptor.id}.enabled"
            enabled = configuration.get(config_key, descriptor.enabled_by_default)
            
            if enabled:
                yield descriptor
    
    @classmethod
    def count(cls) -> int:
        """Возвращает количество зарегистрированных коллекторов."""
        return len(cls._descriptors)
    
    @classmethod
    def clear(cls) -> None:
        """Очищает реестр (для тестирования)."""
        cls._descriptors.clear()
    
    @classmethod
    def is_registered(cls, collector_id: str) -> bool:
        """Проверяет, зарегистрирован ли коллектор."""
        return collector_id in cls._descriptors
    
    @classmethod
    def get_category_map(cls) -> Dict[str, str]:
        """
        ES-1.8.2: Строит category_map автоматически из Descriptor.
        
        Pipeline не строит map вручную — категория идёт из Descriptor.
        
        Returns:
            Dict[collector_id, default_category]
        """
        return {
            descriptor.id: descriptor.default_category
            for descriptor in cls._descriptors.values()
        }


# ==============================================================================
# Декоратор для автоматической регистрации
# ==============================================================================

def passive_collector(
    id: str,
    name: str,
    version: str,
    protocol: str,
    category: str = "passive",
    priority: int = 100,
    enabled_by_default: bool = True,
    capabilities: tuple = (),
    default_category: str = "identity"  # ES-1.8.2: Категория для нормализации
):
    """
    Декоратор для автоматической регистрации Passive Collector.
    
    ES-1.8.2: Добавлен параметр default_category.
    
    Использование:
        @passive_collector(
            id="dns",
            name="DNS Collector",
            version="1.0.0",
            protocol="DNS",
            priority=10,
            enabled_by_default=True,
            capabilities=("dns_resolution", "hostname_discovery"),
            default_category="identity"  # ES-1.8.2
        )
        class DNSCollector(BasePassiveCollector):
            def observe(self, ips, context):
                ...
    
    Args:
        id: Уникальный идентификатор
        name: Человекочитаемое имя
        version: Версия коллектора
        protocol: Протокол
        category: Категория (по умолчанию "passive")
        priority: Приоритет (меньше = раньше)
        enabled_by_default: Включён ли по умолчанию
        capabilities: Кортеж возможностей
        default_category: Категория для нормализации (ES-1.8.2)
    """
    def decorator(cls):
        # Создаём дескриптор с collector_cls и default_category
        descriptor = PassiveCollectorDescriptor(
            id=id,
            name=name,
            version=version,
            protocol=protocol,
            category=category,
            priority=priority,
            enabled_by_default=enabled_by_default,
            capabilities=tuple(capabilities),
            collector_cls=cls,
            default_category=default_category  # ES-1.8.2
        )
        
        # Регистрируем в реестре
        PassiveRegistry.register(descriptor)
        
        # Добавляем дескриптор к классу (для самоодокументирования)
        cls.descriptor = descriptor
        
        return cls
    
    return decorator
