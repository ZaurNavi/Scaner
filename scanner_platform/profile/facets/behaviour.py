#!/usr/bin/env python3
"""Behaviour Facet — поведение устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class BehaviourFacet(BaseFacet):
    """Behaviour Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "behaviour"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Behaviour Facet через Facade."""
        behaviour_facts = self._facade.get_behaviour_facts(device_id)
        
        if not behaviour_facts:
            return {"facts_count": 0, "categories": [], "avg_confidence": 0.0}
        
        return {
            "facts_count": len(behaviour_facts),
            "categories": list(set(f.category for f in behaviour_facts)),
            "avg_confidence": sum(f.confidence for f in behaviour_facts) / len(behaviour_facts)
        }
