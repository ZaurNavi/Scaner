#!/usr/bin/env python3
"""
Passive Registry — автоматическая регистрация Passive Collectors.
ES-1.8.0: Lazy Registration + Factory Pattern.

Registry хранит только дескрипторы и фабрики (классы).
Экземпляры создаются только при вызове get_all(configuration).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterator, List, Optional, Type

from configuration import ConfigurationManager


@dataclass(frozen=True)
class PassiveCollectorDescriptor:
    """
    Метаданные Passive Collector'а.
    
    Минимальный набор:
    - id: уникальный идентификатор
    - name: человекочитаемое имя
    - version: версия коллектора
    - protocol: протокол (DNS, mDNS, LLMNR, NBNS и т.д.)
    - category: категория (passive)
    - priority: приоритет (меньше = раньше)
    - enabled_by_default: включён ли по умолчанию
    - capabilities: список возможностей
    """
    id: str
    name: str
    version: str
    protocol: str
    category: str = "passive"
    priority: int = 100
    enabled_by_default: bool = True
    capabilities: tuple = ()


class PassiveRegistry:
    """
    Реестр Passive Collectors.
    
    v1.8.0: Lazy Registration Pattern.
    - Хранит только дескрипторы и фабрики
    - Экземпляры создаются при вызове get_all(configuration)
    - Автоматическая регистрация через декоратор @passive_collector
    """
    
    _descriptors: Dict[str, PassiveCollectorDescriptor] = {}
    _factories: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, descriptor: PassiveCollectorDescriptor, factory: Type) -> None:
        """
        Регистрирует Passive Collector в реестре.
        
        Args:
            descriptor: Метаданные коллектора
            factory: Класс коллектора (фабрика)
        """
        if descriptor.id in cls._descriptors:
            raise ValueError(f"Passive Collector '{descriptor.id}' already registered")
        
        cls._descriptors[descriptor.id] = descriptor
        cls._factories[descriptor.id] = factory
    
    @classmethod
    def get(cls, collector_id: str, configuration: ConfigurationManager):
        """
        Получает экземпляр конкретного коллектора через Factory.
        
        Args:
            collector_id: ID коллектора
            configuration: ConfigurationManager для DI
        
        Returns:
            Экземпляр BasePassiveCollector
        
        Raises:
            KeyError: Если коллектор не зарегистрирован
        """
        if collector_id not in cls._factories:
            raise KeyError(f"Passive Collector '{collector_id}' not registered")
        
        factory = cls._factories[collector_id]
        return factory(configuration)
    
    @classmethod
    def get_all(cls, configuration: ConfigurationManager) -> List:
        """
        Получает экземпляры всех коллекторов, отсортированные по приоритету.
        
        Args:
            configuration: ConfigurationManager для DI
        
        Returns:
            Список экземпляров BasePassiveCollector
        """
        # Сортируем по priority (меньше = раньше)
        sorted_ids = sorted(
            cls._descriptors.keys(),
            key=lambda x: cls._descriptors[x].priority
        )
        
        return [cls._factories[cid](configuration) for cid in sorted_ids]
    
    @classmethod
    def iter_enabled(cls, configuration: ConfigurationManager) -> Iterator:
        """
        Итерирует только включённые коллекторы.
        
        Args:
            configuration: ConfigurationManager для DI
        
        Yields:
            Экземпляры BasePassiveCollector
        """
        sorted_ids = sorted(
            cls._descriptors.keys(),
            key=lambda x: cls._descriptors[x].priority
        )
        
        for cid in sorted_ids:
            descriptor = cls._descriptors[cid]
            
            # Проверяем enabled_by_default из дескриптора
            # И опционально из Configuration Layer
            config_key = f"fingerprint.collectors.{cid}.enabled"
            enabled = configuration.get(config_key, descriptor.enabled_by_default)
            
            if enabled:
                yield cls._factories[cid](configuration)
    
    @classmethod
    def get_descriptor(cls, collector_id: str) -> Optional[PassiveCollectorDescriptor]:
        """Получает дескриптор коллектора по ID."""
        return cls._descriptors.get(collector_id)
    
    @classmethod
    def get_all_descriptors(cls) -> Dict[str, PassiveCollectorDescriptor]:
        """Получает все дескрипторы."""
        return cls._descriptors.copy()
    
    @classmethod
    def count(cls) -> int:
        """Возвращает количество зарегистрированных коллекторов."""
        return len(cls._descriptors)
    
    @classmethod
    def clear(cls) -> None:
        """Очищает реестр (для тестирования)."""
        cls._descriptors.clear()
        cls._factories.clear()


def passive_collector(
    id: str,
    name: str,
    version: str,
    protocol: str,
    category: str = "passive",
    priority: int = 100,
    enabled_by_default: bool = True,
    capabilities: tuple = ()
):
    """
    Декоратор для автоматической регистрации Passive Collector.
    
    Использование:
        @passive_collector(
            id="dns",
            name="DNS Collector",
            version="1.0.0",
            protocol="DNS",
            priority=10,
            enabled_by_default=True,
            capabilities=("dns_resolution",)
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
    """
    def decorator(cls):
        # Создаём дескриптор
        descriptor = PassiveCollectorDescriptor(
            id=id,
            name=name,
            version=version,
            protocol=protocol,
            category=category,
            priority=priority,
            enabled_by_default=enabled_by_default,
            capabilities=tuple(capabilities)
        )
        
        # Регистрируем в реестре
        PassiveRegistry.register(descriptor, cls)
        
        # Добавляем дескриптор к классу
        cls.descriptor = descriptor
        
        return cls
    
    return decorator
