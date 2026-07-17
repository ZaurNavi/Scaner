#!/usr/bin/env python3
"""Base Facet — базовый класс для всех Facets."""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFacet(ABC):
    """Базовый класс для всех Facets."""
    
    @abstractmethod
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Facet для устройства."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя Facet."""
        pass
