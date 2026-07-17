#!/usr/bin/env python3
"""Base Facet — базовый класс для всех Facets."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ...knowledge.service import KnowledgeService

class BaseFacet(ABC):
    """
    Базовый класс для всех Facets.
    
    Каждый Facet отвечает только за свою область.
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service
    
    @abstractmethod
    def build(self, device_id: str) -> Dict[str, Any]:
        """
        Строит Facet для устройства.
        
        Args:
            device_id: Идентификатор устройства
        
        Returns:
            Dict[str, Any]: Данные Facet
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя Facet."""
        pass
