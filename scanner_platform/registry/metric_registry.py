#!/usr/bin/env python3
"""Metric Registry."""
from dataclasses import dataclass
from typing import Dict, Callable, List, Any
from platform.timeline.models import Timeline

@dataclass
class MetricDescriptor:
    """Дескриптор метрики."""
    id: str
    builder: Callable[[Timeline], Any]
    description: str
    dependencies: List[str]
    version: str = "1.0.0"

class MetricRegistry:
    """Централизованный реестр метрик."""
    
    _metrics: Dict[str, MetricDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: MetricDescriptor):
        """Регистрирует метрику."""
        cls._metrics[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, metric_id: str) -> MetricDescriptor:
        """Получает дескриптор метрики."""
        return cls._metrics.get(metric_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, MetricDescriptor]:
        """Получает все метрики."""
        return cls._metrics.copy()
    
    @classmethod
    def build(cls, timeline: Timeline) -> Dict[str, Any]:
        """Вычисляет все метрики из Timeline."""
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
        """Проверяет зависимости метрик."""
        errors = []
        
        for metric_id, descriptor in cls._metrics.items():
            for dep in descriptor.dependencies:
                if not dep.startswith("timeline."):
                    errors.append(f"Metric {metric_id} has invalid dependency: {dep}")
        
        return errors
