#!/usr/bin/env python3
"""Base Event Rule - базовый класс для правил генерации событий."""
from abc import ABC, abstractmethod
from typing import Tuple, Any
from datetime import datetime
from ...diff.models import Change

class BaseEventRule(ABC):
    """Базовый класс для всех Event Rules."""
    
    @abstractmethod
    def supports(self, change: Change) -> bool:
        """Проверяет, может ли правило обработать это изменение."""
        pass
    
    @abstractmethod
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[Any, ...]:
        """
        Генерирует события для данного изменения.
        Возвращает tuple из 0..N событий.
        device_uuid и occurred_at передаются из Generator для детерминированности.
        """
        pass
