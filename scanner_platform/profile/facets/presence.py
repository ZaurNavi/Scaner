#!/usr/bin/env python3
"""Presence Facet — присутствие устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService
from ...knowledge.query import KnowledgeQuery

class PresenceFacet(BaseFacet):
    """Presence Facet — агрегирует факты Presence."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "presence"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Presence Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        # Query по категории presence
        query = KnowledgeQuery(category="presence")
        presence_facts = query.execute(snapshot)
        
        return {
            "facts_count": len(presence_facts),
            "categories": list(set(f.category for f in presence_facts)),
            "avg_confidence": sum(f.confidence for f in presence_facts) / len(presence_facts) if presence_facts else 0.0
        }
