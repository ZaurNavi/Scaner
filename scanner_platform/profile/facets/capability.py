#!/usr/bin/env python3
"""Capability Facet — возможности устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.service import KnowledgeService
from ..capability.resolver import CapabilityResolver

class CapabilityFacet(BaseFacet):
    """Capability Facet — агрегирует доступные возможности."""
    
    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__(knowledge_service)
    
    def get_name(self) -> str:
        return "capability"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """Строит Capability Facet."""
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            return {}
        
        capabilities = CapabilityResolver.resolve(snapshot)
        available_count = sum(1 for is_available in capabilities.values() if is_available)
        
        return {
            "total": len(capabilities),
            "available": available_count,
            "capabilities": capabilities
        }
