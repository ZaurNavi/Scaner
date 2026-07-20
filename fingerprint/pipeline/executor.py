#!/usr/bin/env python3
"""
CollectorExecutor.
ES-1.8.3: Ожидает List[Observation] от всех коллекторов.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from configuration import ConfigurationManager
from ..normalization.models import Observation
from ..collectors.registry import PassiveRegistry
from ..collectors.factory import PassiveCollectorFactory


class CollectorExecutor(ABC):
    @abstractmethod
    def run(self, ips: List[str], configuration: ConfigurationManager) -> List[Observation]:
        pass


class PassiveCollectorExecutor(CollectorExecutor):
    def run(self, ips: List[str], configuration: ConfigurationManager) -> List[Observation]:
        all_observations = []
        enabled_descriptors = list(PassiveRegistry.iter_enabled_descriptors(configuration))

        for descriptor in enabled_descriptors:
            collector = PassiveCollectorFactory.create(descriptor, configuration)
            # ES-1.8.3: observe() возвращает List[Observation]
            observations = collector.observe(ips, context={})
            all_observations.extend(observations)

        return all_observations
