#!/usr/bin/env python3
"""Usage Facet — использование сети."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService
from ...knowledge.query import KnowledgeQuery

class UsageFacet(BaseFacet):
    """Usage Facet — агрегирует факты Usage."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "usage"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Usage Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        query = KnowledgeQuery(category="usage")
        usage_facts = query.execute(snapshot)
        
        return {
            "facts_count": len(usage_facts),
            "categories": list(set(f.category for f in usage_facts)),
            "avg_confidence": sum(f.confidence for f in usage_facts) / len(usage_facts) if usage_facts else 0.0
        }
