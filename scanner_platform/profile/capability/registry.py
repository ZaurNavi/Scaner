#!/usr/bin/env python3
"""Capability Registry — реестр возможностей платформы."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

@dataclass
class CapabilityDescriptor:
    """Дескриптор возможности платформы."""
    id: str
    description: str
    requires_categories: List[str] = field(default_factory=list)
    requires_facts: List[str] = field(default_factory=list)
    optional_categories: List[str] = field(default_factory=list)
    minimum_confidence: float = 0.0
    version: str = "1.0.0"

class CapabilityRegistry:
    """Централизованный реестр возможностей."""
    
    _capabilities: Dict[str, CapabilityDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: CapabilityDescriptor):
        """Регистрирует возможность."""
        cls._capabilities[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, capability_id: str) -> Optional[CapabilityDescriptor]:
        """Получает дескриптор возможности."""
        return cls._capabilities.get(capability_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, CapabilityDescriptor]:
        """Получает все возможности."""
        return cls._capabilities.copy()
