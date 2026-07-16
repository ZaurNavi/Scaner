#!/usr/bin/env python3
"""Базовый интерфейс для всех Builder'ов."""
from abc import ABC, abstractmethod
from typing import Any, Dict

class Builder(ABC):
    """Базовый класс для всех Builder'ов платформы."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя Builder'а."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Версия Builder'а."""
        pass
    
    @abstractmethod
    def build(self, input_data: Any) -> Any:
        """
        Выполняет построение.
        
        Args:
            input_data: Входные данные
        
        Returns:
            Результат построения
        """
        pass
