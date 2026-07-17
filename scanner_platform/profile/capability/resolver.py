#!/usr/bin/env python3
"""Capability Resolver — определяет доступные возможности устройства."""
from typing import Dict, List, Any
from .registry import CapabilityRegistry, CapabilityDescriptor
from ...knowledge.snapshot import KnowledgeSnapshot

class CapabilityResolver:
    """
    Определяет доступные возможности на основе Knowledge Snapshot.
    
    Не вычисляет Capability, только проверяет доступность.
    """
    
    @staticmethod
    def resolve(snapshot: KnowledgeSnapshot) -> Dict[str, bool]:
        """
        Определяет доступность всех Capability для устройства.
        
        Args:
            snapshot: Knowledge Snapshot устройства
        
        Returns:
            Dict[str, bool]: {capability_id: is_available}
        """
        capabilities = CapabilityRegistry.get_all()
        results = {}
        
        # Собираем доступные категории и факты
        available_categories = set()
        available_facts = set()
        avg_confidence = 0.0
        
        if snapshot.facts:
            available_categories = set(f.category for f in snapshot.facts)
            available_facts = set(f.id for f in snapshot.facts)
            avg_confidence = sum(f.confidence for f in snapshot.facts) / len(snapshot.facts)
        
        for cap_id, descriptor in capabilities.items():
            is_available = CapabilityResolver._check_availability(
                descriptor, available_categories, available_facts, avg_confidence
            )
            results[cap_id] = is_available
        
        return results
    
    @staticmethod
    def _check_availability(
        descriptor: CapabilityDescriptor,
        available_categories: set,
        available_facts: set,
        avg_confidence: float
    ) -> bool:
        """Проверяет доступность конкретной Capability."""
        # Проверка required_categories
        for req_cat in descriptor.requires_categories:
            if req_cat not in available_categories:
                return False
        
        # Проверка required_facts
        for req_fact in descriptor.requires_facts:
            if req_fact not in available_facts:
                return False
        
        # Проверка minimum_confidence
        if avg_confidence < descriptor.minimum_confidence:
            return False
        
        return True
