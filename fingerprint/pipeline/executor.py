#!/usr/bin/env python3
"""
CollectorExecutor.
ES-1.8.3: Ожидает List[Observation] от всех коллекторов.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from configuration import ConfigurationManager
from models import Device
from ..normalization.models import Observation
from ..collectors.registry import PassiveRegistry
from ..collectors.factory import PassiveCollectorFactory
from ..active.registry import get_collectors


# ==============================================================================
# Базовый интерфейс
# ==============================================================================

class CollectorExecutor(ABC):
    @abstractmethod
    def run(self, ips: List[str], configuration: ConfigurationManager, devices: List[Device] = None) -> List[Observation]:
        pass


# ==============================================================================
# PassiveCollectorExecutor — запускает Passive Collectors
# ==============================================================================

class PassiveCollectorExecutor(CollectorExecutor):
    def run(self, ips: List[str], configuration: ConfigurationManager, devices: List[Device] = None) -> List[Observation]:
        all_observations = []
        enabled_descriptors = list(PassiveRegistry.iter_enabled_descriptors(configuration))

        for descriptor in enabled_descriptors:
            collector = PassiveCollectorFactory.create(descriptor, configuration)
            # ES-1.8.3: observe() возвращает List[Observation]
            observations = collector.observe(ips, context={})
            all_observations.extend(observations)

        return all_observations


# ==============================================================================
# ActiveCollectorExecutor — запускает Active Collectors
# ==============================================================================

class ActiveCollectorExecutor(CollectorExecutor):
    """
    ES-1.8.3: Запускает Active Collectors и собирает List[Observation].
    """

    def run(self, ips: List[str], configuration: ConfigurationManager, devices: List[Device] = None) -> List[Observation]:
        if not devices:
            return []

        all_observations = []
        collectors = get_collectors(configuration)

        for collector in collectors:
            try:
                # scan() возвращает List[Observation]
                observations = collector.scan(devices, context={})
                all_observations.extend(observations)
            except Exception as e:
                print(f"         • ⚠️ Active Collector '{collector.source_name}' failed: {e}")
                continue

        return all_observations


# ==============================================================================
# CompositeCollectorExecutor — объединяет Passive + Active
# ==============================================================================

class CompositeCollectorExecutor(CollectorExecutor):
    """
    ES-1.8.3: Объединяет Passive и Active Collectors в единый поток Observation.
    """

    def __init__(self):
        self.passive_executor = PassiveCollectorExecutor()
        self.active_executor = ActiveCollectorExecutor()

    def run(self, ips: List[str], configuration: ConfigurationManager, devices: List[Device] = None) -> List[Observation]:
        all_observations = []

        # 1. Passive Collectors
        print("         • Running Passive Collectors...")
        passive_obs = self.passive_executor.run(ips, configuration, devices)
        all_observations.extend(passive_obs)
        print(f"              → {len(passive_obs)} observations")

        # 2. Active Collectors
        print("         • Running Active Collectors...")
        active_obs = self.active_executor.run(ips, configuration, devices)
        all_observations.extend(active_obs)
        print(f"              → {len(active_obs)} observations")

        return all_observations
