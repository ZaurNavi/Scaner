#!/usr/bin/env python3
"""
Passive Collector Factory — фабрика для создания экземпляров коллекторов.
ES-1.8.0: Отвечает ТОЛЬКО за создание экземпляров (SRP).

Архитектура:
    Registry → Descriptor → Factory → Collector
"""

from __future__ import annotations

from typing import List

from configuration import ConfigurationManager

from .registry import PassiveRegistry, PassiveCollectorDescriptor


class PassiveCollectorFactory:
    """
    Фабрика для создания экземпляров Passive Collectors.
    
    v1.8.0: Factory отвечает только за создание экземпляров.
    Registry хранит только дескрипторы.
    
    SRP: Factory знает, как создать экземпляр из дескриптора.
    """
    
    @staticmethod
    def create(
        descriptor: PassiveCollectorDescriptor,
        configuration: ConfigurationManager
    ):
        """
        Создаёт экземпляр коллектора из дескриптора.
        
        Args:
            descriptor: Метаданные коллектора
            configuration: ConfigurationManager для DI
        
        Returns:
            Экземпляр BasePassiveCollector
        
        Raises:
            ValueError: Если collector_cls не указан в дескрипторе
        """
        if descriptor.collector_cls is None:
            raise ValueError(
                f"Passive Collector '{descriptor.id}' has no collector_cls. "
                f"Cannot create instance."
            )
        
        # Создаём экземпляр через конструктор с DI
        return descriptor.collector_cls(configuration)
    
    @classmethod
    def create_all(
        cls,
        configuration: ConfigurationManager
    ) -> List:
        """
        Создаёт экземпляры всех коллекторов, отсортированные по приоритету.
        
        Args:
            configuration: ConfigurationManager для DI
        
        Returns:
            Список экземпляров BasePassiveCollector
        """
        descriptors = PassiveRegistry.get_sorted_descriptors()
        return [cls.create(descriptor, configuration) for descriptor in descriptors]
    
    @classmethod
    def create_enabled(
        cls,
        configuration: ConfigurationManager
    ) -> List:
        """
        Создаёт экземпляры только включённых коллекторов.
        
        Args:
            configuration: ConfigurationManager для DI
        
        Returns:
            Список экземпляров BasePassiveCollector
        """
        descriptors = list(PassiveRegistry.iter_enabled_descriptors(configuration))
        return [cls.create(descriptor, configuration) for descriptor in descriptors]
