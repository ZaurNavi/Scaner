#!/usr/bin/env python3
"""Provider Registry."""
from dataclasses import dataclass
from typing import Dict, Type, List

@dataclass
class ProviderDescriptor:
    """Дескриптор Provider'а."""
    id: str
    version: str
    priority: int
    dependencies: List[str]
    provider_class: Type

class ProviderRegistry:
    """Централизованный реестр Providers."""
    
    _providers: Dict[str, ProviderDescriptor] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: Type, version: str = "1.0.0", 
                 priority: int = 10, dependencies: List[str] = None):
        """Регистрирует Provider."""
        cls._providers[name] = ProviderDescriptor(
            id=name, version=version, priority=priority,
            dependencies=dependencies or [], provider_class=provider_class
        )
    
    @classmethod
    def get(cls, name: str) -> ProviderDescriptor:
        """Получает дескриптор Provider'а."""
        return cls._providers.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, ProviderDescriptor]:
        """Получает все Providers."""
        return cls._providers.copy()
