#!/usr/bin/env python3
"""
Базовый интерфейс для источников трафика.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

from ..models import TrafficInfo


class TrafficSource(ABC):
    """
    Абстрактный базовый класс для источников трафика.
    """
    
    def __init__(self):
        # (Пункт 10 и 12)
        self.priority: int = 100
        self.stats: dict[str, Any] = {
            "devices": 0,
            "elapsed_ms": 0.0,
            "errors": 0
        }

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    def initialize(self) -> None:
        """Вызывается один раз при старте цикла сбора."""
        pass

    def shutdown(self) -> None:
        """Вызывается один раз при завершении цикла сбора."""
        pass

    @abstractmethod
    def collect_all(self, cycle_timestamp: datetime, target_ips: list[str]) -> Dict[str, TrafficInfo]:
        """
        Собирает данные. 
        (Пункт 1: принимает target_ips для фильтрации)
        (Пункт 4: принимает единый cycle_timestamp)
        """
        pass
