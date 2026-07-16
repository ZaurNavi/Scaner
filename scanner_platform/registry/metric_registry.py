#!/usr/bin/env python3
"""Metric Registry."""
from dataclasses import dataclass
from typing import Dict, Callable, List, Any
from ..timeline.models import Timeline  # <-- ИСПРАВЛЕНО

@dataclass
class MetricDescriptor:
    id: str
    builder: Callable[[Timeline], Any]
    description: str
    dependencies: List[str]
    version: str = "1.0.0"

class MetricRegistry:
    _metrics: Dict[str, MetricDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: MetricDescriptor):
        cls._metrics[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, metric_id: str) -> MetricDescriptor:
        return cls._metrics.get(metric_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, MetricDescriptor]:
        return cls._metrics.copy()
    
    @classmethod
    def build(cls, timeline: Timeline) -> Dict[str, Any]:
        metrics = {}
        for metric_id, descriptor in cls._metrics.items():
            try:
                value = descriptor.builder(timeline)
                metrics[metric_id] = value
            except Exception as e:
                print(f"  [METRICS] ⚠️ Failed to build {metric_id}: {e}")
        return metrics
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        errors = []
        for metric_id, descriptor in cls._metrics.items():
            for dep in descriptor.dependencies:
                if not dep.startswith("timeline."):
                    errors.append(f"Metric {metric_id} has invalid dependency: {dep}")
        return errors
