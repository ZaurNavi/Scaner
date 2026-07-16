#!/usr/bin/env python3
"""Features Builder."""
from datetime import datetime
from typing import Dict, Any
from .base import Builder
from platform.registry.feature_registry import FeatureRegistry

class FeaturesBuilder(Builder):
    """Вычисляет признаки из метрик."""
    
    @property
    def name(self) -> str:
        return "features_builder"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def build(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Вычисляет все признаки из метрик."""
        metrics = metrics_data.get("metrics", {})
        features = FeatureRegistry.build(metrics)
        
        return {
            "features": features,
            "generated_at": datetime.now(),
            "metrics_generated_at": metrics_data.get("generated_at")
        }
