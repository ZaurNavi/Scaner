#!/usr/bin/env python3
"""Metrics Builder: координатор (Замечание №1, №12)."""
from datetime import datetime
from typing import Dict
from ..models import PresenceMetricSet, PresenceQuality
from .absolute_metrics import build_absolute_metrics
from .distribution_metrics import build_distribution_metrics

class MetricsBuilder:
    """Координирует вычисление всех метрик."""
    
    def build(self, raw_data: dict) -> PresenceMetricSet:
        """Вычисляет все метрики и возвращает PresenceMetricSet."""
        all_metrics = {}
        
        # Absolute metrics
        all_metrics.update(build_absolute_metrics(raw_data))
        
        # Distribution metrics
        all_metrics.update(build_distribution_metrics(raw_data))
        
        # Вычисляем общее качество
        total_coverage = sum(m.quality.coverage for m in all_metrics.values()) / len(all_metrics) if all_metrics else 0.0
        total_confidence = sum(m.quality.confidence for m in all_metrics.values()) / len(all_metrics) if all_metrics else 0.0
        
        return PresenceMetricSet(
            metrics=all_metrics,
            generated_at=datetime.now(),
            coverage=total_coverage,
            quality=PresenceQuality(coverage=total_coverage, confidence=total_confidence)
        )
