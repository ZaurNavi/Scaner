#!/usr/bin/env python3
"""Summary Facet — краткое описание устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class SummaryFacet(BaseFacet):
    """Summary Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "summary"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Summary Facet через Facade."""
        return self._facade.get_summary(device_id)
