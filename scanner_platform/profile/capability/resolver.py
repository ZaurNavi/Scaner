#!/usr/bin/env python3
"""Capability Resolver — определяет доступные возможности."""
from typing import Dict
from .registry import CapabilityRegistry
from ..profile import UnifiedDeviceProfile

class CapabilityResolver:
    """
    Определяет доступные возможности на основе Profile.
    
    Работает с Profile, а не со Snapshot.
    """
    
    @staticmethod
    def resolve(profile: UnifiedDeviceProfile) -> Dict[str, bool]:
        """
        Определяет доступность всех Capability для устройства.
        
        Args:
            profile: UnifiedDeviceProfile
        
        Returns:
            Dict[str, bool]: {capability_id: is_available}
        """
        capabilities = CapabilityRegistry.get_all()
        results = {}
        
        # Извлекаем данные из Profile
        available_categories = set(profile.categories.__dict__.keys())
        avg_confidence = profile.confidence.overall
        
        for cap_id, descriptor in capabilities.items():
            is_available = CapabilityResolver._check_availability(
                descriptor, available_categories, avg_confidence
            )
            results[cap_id] = is_available
        
        return results
    
    @staticmethod
    def _check_availability(
        descriptor,
        available_categories: set,
        avg_confidence: float
    ) -> bool:
        """Проверяет доступность конкретной Capability."""
        # Проверка required_categories
        for req_cat in descriptor.requires_categories:
            if req_cat not in available_categories:
                return False
        
        # Проверка minimum_confidence
        if avg_confidence < descriptor.minimum_confidence:
            return False
        
        return True
