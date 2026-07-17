#!/usr/bin/env python3
"""Presence Facet — присутствие устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class PresenceFacet(BaseFacet):
    """Presence Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "presence"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Presence Facet через Facade."""
        presence_facts = self._facade.get_presence_facts(device_id)
        
        if not presence_facts:
            return {"facts_count": 0, "categories": [], "avg_confidence": 0.0}
        
        return {
            "facts_count": len(presence_facts),
            "categories": list(set(f.category for f in presence_facts)),
            "avg_confidence": sum(f.confidence for f in presence_facts) / len(presence_facts)
        }
