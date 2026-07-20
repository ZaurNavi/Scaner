#!/usr/bin/env python3
"""
Base Passive Collector.
ES-1.8.3: Единый контракт — List[Observation].
Legacy-система (collect_all, FingerprintResult, CollectedData) удалена.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from configuration import ConfigurationManager
from ..normalization.models import ObservationCategory


class BasePassiveCollector(ABC):
    """
    Абстрактный базовый класс для всех Passive Collectors.
    ES-1.8.3: Единый контракт — observe() возвращает List[Observation].
    """
    
    descriptor: Any = None
    category: ObservationCategory = ObservationCategory.IDENTITY
    
    def __init__(self, configuration: ConfigurationManager):
        self.config = configuration
    
    @abstractmethod
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> List:
        """
        ES-1.8.3: Возвращает List[Observation].
        """
        pass
    
    @property
    def id(self) -> str:
        return self.descriptor.id if self.descriptor else self.__class__.__name__.lower()
    
    @property
    def name(self) -> str:
        return self.descriptor.name if self.descriptor else self.__class__.__name__
    
    @property
    def version(self) -> str:
        return self.descriptor.version if self.descriptor else "0.0.0"
    
    @property
    def protocol(self) -> str:
        return self.descriptor.protocol if self.descriptor else "unknown"
    
    @property
    def capabilities(self) -> tuple:
        return self.descriptor.capabilities if self.descriptor else ()
