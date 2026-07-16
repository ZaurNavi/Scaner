#!/usr/bin/env python3
"""Timeline Provider Interface с единой структурой возврата."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from .models import TimelineEvent

@dataclass
class ProviderResult:
    """Единая структура возврата для всех Providers."""
    events: List[TimelineEvent] = field(default_factory=list)
    quality: float = 0.9
    statistics: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

class TimelineProvider(ABC):
    """Базовый интерфейс для всех Timeline Providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Версия провайдера."""
        pass
    
    @abstractmethod
    def extract(self, device_id: str) -> ProviderResult:
        """
        Извлекает сырые события и преобразует их в ProviderResult.
        
        Args:
            device_id: Идентификатор устройства
        
        Returns:
            ProviderResult: Единая структура с событиями
        """
        pass
