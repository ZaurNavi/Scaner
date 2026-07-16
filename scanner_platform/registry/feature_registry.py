#!/usr/bin/env python3
"""Feature Registry."""
from dataclasses import dataclass
from typing import Dict, Callable, List, Any, Type

@dataclass
class FeatureDescriptor:
    """Дескриптор признака."""
    id: str
    engine: str
    type: Type
    builder: Callable[[Dict[str, Any]], Any]
    description: str
    dependencies: List[str]
    version: str = "1.0.0"

class FeatureRegistry:
    """Централизованный реестр признаков."""
    
    _features: Dict[str, FeatureDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: FeatureDescriptor):
        """Регистрирует признак."""
        cls._features[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, feature_id: str) -> FeatureDescriptor:
        """Получает дескриптор признака."""
        return cls._features.get(feature_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, FeatureDescriptor]:
        """Получает все признаки."""
        return cls._features.copy()
    
    @classmethod
    def get_by_engine(cls, engine: str) -> Dict[str, FeatureDescriptor]:
        """Получает признаки для конкретного движка."""
        return {k: v for k, v in cls._features.items() if v.engine == engine}
    
    @classmethod
    def build(cls, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Вычисляет все признаки из метрик."""
        features = {}
        
        for feature_id, descriptor in cls._features.items():
            try:
                value = descriptor.builder(metrics)
                features[feature_id] = value
            except Exception as e:
                print(f"  [FEATURES] ⚠️ Failed to build {feature_id}: {e}")
        
        return features
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        """Проверяет зависимости признаков."""
        errors = []
        
        for feature_id, descriptor in cls._features.items():
            for dep in descriptor.dependencies:
                if dep not in MetricRegistry.get_all():
                    errors.append(f"Feature {feature_id} depends on unknown metric: {dep}")
        
        return errors

from platform.registry.metric_registry import MetricRegistry
