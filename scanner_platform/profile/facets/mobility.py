#!/usr/bin/env python3
"""Mobility Facet — перемещение устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService
from ...knowledge.query import KnowledgeQuery

class MobilityFacet(BaseFacet):
    """Mobility Facet — агрегирует факты Mobility."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "mobility"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Mobility Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        query = KnowledgeQuery(category="mobility")
        mobility_facts = query.execute(snapshot)
        
        return {
            "facts_count": len(mobility_facts),
            "categories": list(set(f.category for f in mobility_facts)),
            "avg_confidence": sum(f.confidence for f in mobility_facts) / len(mobility_facts) if mobility_facts else 0.0
        }
