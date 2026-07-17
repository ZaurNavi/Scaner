#!/usr/bin/env python3
"""Capability Facet — возможности устройства."""
from typing import Dict, Any
from .base import BaseFacet
from ...knowledge.facade import KnowledgeFacade
from ..capability.resolver import CapabilityResolver

class CapabilityFacet(BaseFacet):
    """Capability Facet — через KnowledgeFacade."""
    
    def __init__(self, facade: KnowledgeFacade):
        self._facade = facade
    
    def get_name(self) -> str:
        return "capability"
    
    def build(self, device_id: str) -> Dict[str, Any]:
        """
        Строит Capability Facet.
        
        Примечание: CapabilityResolver.resolve() будет вызван
        позже в Builder с уже готовым Profile.
        """
        return {
            "total": 0,
            "available": 0,
            "capabilities": {}
        }
