#!/usr/bin/env python3
"""PlatformContext — единственная точка доступа для движков."""
from dataclasses import dataclass
from .bundles import MetricBundle, FeatureBundle, RuleBundle
from ..timeline.models import Timeline

@dataclass
class PlatformContext:
    """
    Контекст, который Platform передаёт движку.
    
    Движок видит ТОЛЬКО:
    - context.timeline
    - context.metrics
    - context.features
    - context.rules
    
    Никаких Registry. Никакой инфраструктуры.
    """
    device_id: str
    timeline: Timeline
    metrics: MetricBundle
    features: FeatureBundle
    rules: RuleBundle
