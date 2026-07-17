#!/usr/bin/env python3
"""Behaviour Facet — поведение устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService
from ...knowledge.query import KnowledgeQuery

class BehaviourFacet(BaseFacet):
    """Behaviour Facet — агрегирует факты Behaviour."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "behaviour"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Behaviour Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        query = KnowledgeQuery(category="behaviour")
        behaviour_facts = query.execute(snapshot)
        
        return {
            "facts_count": len(behaviour_facts),
            "categories": list(set(f.category for f in behaviour_facts)),
            "avg_confidence": sum(f.confidence for f in behaviour_facts) / len(behaviour_facts) if behaviour_facts else 0.0
        }
