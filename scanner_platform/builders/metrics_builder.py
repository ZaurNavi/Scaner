#!/usr/bin/env python3
"""Metrics Builder."""
from datetime import datetime
from typing import Dict, Any
from .base import Builder
from platform.timeline.models import Timeline
from platform.registry.metric_registry import MetricRegistry

class MetricsBuilder(Builder):
    """Вычисляет метрики из Timeline."""
    
    @property
    def name(self) -> str:
        return "metrics_builder"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def build(self, timeline: Timeline) -> Dict[str, Any]:
        """Вычисляет все метрики из Timeline."""
        metrics = MetricRegistry.build(timeline)
        
        return {
            "metrics": metrics,
            "generated_at": datetime.now(),
            "timeline_device_id": timeline.device_id
        }
