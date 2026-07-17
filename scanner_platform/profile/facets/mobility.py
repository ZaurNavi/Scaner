#!/usr/bin/env python3
"""Mobility Facet — перемещение устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class MobilityFacet(BaseFacet):
    """Mobility Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "mobility"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Mobility Facet через Facade."""
        mobility_facts = self._facade.get_mobility_facts(device_id)
        
        if not mobility_facts:
            return {"facts_count": 0, "categories": [], "avg_confidence": 0.0}
        
        return {
            "facts_count": len(mobility_facts),
            "categories": list(set(f.category for f in mobility_facts)),
            "avg_confidence": sum(f.confidence for f in mobility_facts) / len(mobility_facts)
        }
