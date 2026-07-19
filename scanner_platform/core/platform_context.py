#!/usr/bin/env python3
"""PlatformContext — единственная точка доступа для движков."""
from dataclasses import dataclass
from typing import Optional
from .bundles import MetricBundle, FeatureBundle, RuleBundle
from ..timeline.models import Timeline

# v1.6.9.2: Configuration Layer Integration
from configuration import ConfigurationManager


@dataclass
class PlatformContext:
    """
    Контекст, который Platform передаёт движку.
    
    v1.6.9.2: Движок видит:
    - context.configuration — единый источник конфигурации
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
    configuration: ConfigurationManager  # v1.6.9.2: обязательное поле
