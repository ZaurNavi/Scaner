#!/usr/bin/env python3
"""Реестры с автоматической регистрацией."""
from dataclasses import dataclass
from typing import Dict, Type, Callable, List, Optional

@dataclass
class ProviderDescriptor:
    id: str
    version: str
    priority: int
    dependencies: List[str]
    provider_class: Type

@dataclass
class FeatureDescriptor:
    id: str
    version: str
    builder: Callable
    dependencies: List[str]
    output_type: str

class ProviderRegistry:
    _providers: Dict[str, ProviderDescriptor] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type, version: str = "1.0.0", 
                 priority: int = 10, dependencies: List[str] = None):
        cls._providers[name] = ProviderDescriptor(
            id=name, version=version, priority=priority,
            dependencies=dependencies or [], provider_class=provider_class
        )

    @classmethod
    def get_all(cls) -> Dict[str, ProviderDescriptor]:
        return cls._providers.copy()

class FeatureRegistry:
    _features: Dict[str, FeatureDescriptor] = {}

    @classmethod
    def register(cls, feature_id: str, builder_func: Callable, version: str = "1.0.0",
                 dependencies: List[str] = None, output_type: str = "UsageFeature"):
        cls._features[feature_id] = FeatureDescriptor(
            id=feature_id, version=version, builder=builder_func,
            dependencies=dependencies or [], output_type=output_type
        )

    @classmethod
    def get_all(cls) -> Dict[str, FeatureDescriptor]:
        return cls._features.copy()
    
    @classmethod
    def iterate(cls):
        return [(fd.id, fd.builder) for fd in cls._features.values()]

def register_feature(feature_id: str, version: str = "1.0.0", dependencies: List[str] = None):
    def decorator(func: Callable):
        FeatureRegistry.register(feature_id, func, version, dependencies)
        return func
    return decorator
