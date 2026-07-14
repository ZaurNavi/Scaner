#!/usr/bin/env python3
"""
Базовый класс для Infrastructure Controller Collectors.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseControllerCollector(ABC):
    """
    Базовый интерфейс для коллекторов, опрашивающих контроллеры инфраструктуры.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя коллектора (например, 'omada')."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Проверяет, включен ли коллектор в конфигурации."""
        pass

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Выполняет полный цикл сбора данных с контроллера.
        Возвращает единый снапшот: {"sites": [...], "clients": [...], "devices": [...]}
        """
        pass
