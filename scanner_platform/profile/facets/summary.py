#!/usr/bin/env python3
"""Summary Facet — краткое описание устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService

class SummaryFacet(BaseFacet):
    """Summary Facet — агрегирует Summary из Knowledge Snapshot."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "summary"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Summary Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        return dict(snapshot.summary)
