#!/usr/bin/env python3
"""
CollectorExecutor — абстракция между Pipeline и Framework.
ES-1.8.2: Pipeline не знает о Active/Passive Framework.

Архитектура:
Pipeline → CollectorExecutor → Registry → Collectors
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from configuration import ConfigurationManager

from ..collectors.base import Observation
from ..collectors.registry import PassiveRegistry
from ..collectors.factory import PassiveCollectorFactory


class CollectorExecutor(ABC):
    """
    Абстрактный исполнитель коллекторов.
    
    ES-1.8.2:
    - Pipeline не знает о конкретных Framework
    - Executor.run(context) → Observation[]
    - Через год добавятся Remote, Cloud, Replay, PCAP без изменения Pipeline
    """
    
    @abstractmethod
    def run(self, ips: List[str], configuration: ConfigurationManager) -> List[Observation]:
        """
        Запускает коллекторы и возвращает наблюдения.
        
        Args:
            ips: Список IP-адресов
            configuration: ConfigurationManager для DI
        
        Returns:
            Список Observation от всех коллекторов
        """
        pass


class PassiveCollectorExecutor(CollectorExecutor):
    """
    Исполнитель Passive Collectors.
    
    ES-1.8.2:
    - Работает только через PassiveRegistry
    - Не знает о конкретных коллекторах
    - Категория приходит из Descriptor
    """
    
    def run(self, ips: List[str], configuration: ConfigurationManager) -> List[Observation]:
        """
        Запускает Passive Collectors через Registry.
        """
        all_observations = []
        
        # Получаем все включённые дескрипторы из Registry
        enabled_descriptors = list(PassiveRegistry.iter_enabled_descriptors(configuration))
        
        for descriptor in enabled_descriptors:
            # Создаём экземпляр через Factory
            collector = PassiveCollectorFactory.create(descriptor, configuration)
            
            # Запускаем коллектор
            observations_dict = collector.observe(ips, context={})
            
            # Преобразуем dict в list
            for ip, obs in observations_dict.items():
                all_observations.append(obs)
        
        return all_observations
