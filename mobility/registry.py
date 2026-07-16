#!/usr/bin/env python3
"""Реестры для Mobility Engine (Open/Closed Principle)."""
from typing import Dict, Type, Any, Callable

class ProviderRegistry:
    _providers: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type):
        cls._providers[name] = provider_class

    @classmethod
    def get_all(cls) -> Dict[str, Type]:
        return cls._providers.copy()

class FeatureRegistry:
    _features: Dict[str, Callable] = {}

    @classmethod
    def register(cls, feature_id: str, builder_func: Callable):
        cls._features[feature_id] = builder_func

    @classmethod
    def get_all(cls) -> Dict[str, Callable]:
        return cls._features.copy()
