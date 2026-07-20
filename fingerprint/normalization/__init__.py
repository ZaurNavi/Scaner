#!/usr/bin/env python3
"""
Normalization Layer — преобразование Observation в UnifiedObservation.
ES-1.8.1: Единый формат наблюдений независимо от источника данных.

Архитектура:
    Collector → Observation → Normalizer → UnifiedObservation → Knowledge
"""

from .models import Observation, UnifiedObservation, ObservationCategory
from .normalizer import Normalizer
from .registry import RuleRegistry

__all__ = [
    "Observation",
    "UnifiedObservation",
    "ObservationCategory",
    "Normalizer",
    "RuleRegistry",
]
