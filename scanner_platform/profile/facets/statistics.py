#!/usr/bin/env python3
"""Statistics Facet — статистика устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class StatisticsFacet(BaseFacet):
    """Statistics Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "statistics"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Statistics Facet через Facade."""
        return self._facade.get_statistics(device_id)
