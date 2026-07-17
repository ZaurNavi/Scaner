#!/usr/bin/env python3
"""Usage Facet — использование сети."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade

class UsageFacet(BaseFacet):
    """Usage Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "usage"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Usage Facet через Facade."""
        usage_facts = self._facade.get_usage_facts(device_id)
        
        if not usage_facts:
            return {"facts_count": 0, "categories": [], "avg_confidence": 0.0}
        
        return {
            "facts_count": len(usage_facts),
            "categories": list(set(f.category for f in usage_facts)),
            "avg_confidence": sum(f.confidence for f in usage_facts) / len(usage_facts)
        }
