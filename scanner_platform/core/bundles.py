#!/usr/bin/env python3
"""Пакеты данных, которые Platform передаёт движкам."""
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class MetricBundle:
    """Готовый пакет метрик от Platform."""
    metrics: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def get(self, metric_id: str, default=None):
        return self.metrics.get(metric_id, default)
    
    def __getitem__(self, key: str):
        return self.metrics[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.metrics

@dataclass
class FeatureBundle:
    """Готовый пакет признаков от Platform."""
    features: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def get(self, feature_id: str, default=None):
        return self.features.get(feature_id, default)
    
    def __getitem__(self, key: str):
        return self.features[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.features

@dataclass
class RuleBundle:
    """Готовый пакет правил от Platform."""
    rules: List[Any] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
