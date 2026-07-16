#!/usr/bin/env python3
"""Реестры с поддержкой автоматической регистрации (Замечание №11)."""
from typing import Dict, Type, Callable

class ProviderRegistry:
    _providers: Dict[str, Type] = {}

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
    
    @classmethod
    def iterate(cls):
        """Итератор по всем зарегистрированным фичам (Замечание №11)."""
        return cls._features.items()

def register_feature(feature_id: str):
    """Декоратор для автоматической регистрации Feature Builder."""
    def decorator(func: Callable):
        FeatureRegistry.register(feature_id, func)
        return func
    return decorator
