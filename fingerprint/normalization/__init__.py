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

# ... существующие импорты ...
from .factory import ObservationFactory
from .registry import AttributeRegistry, AttributeDescriptor
from .models import ObservationCategory

# ==============================================================================
# ES-1.8.3: Регистрация доменных атрибутов
# ==============================================================================
AttributeRegistry.register(AttributeDescriptor(
    id="hostname", category=ObservationCategory.IDENTITY, value_type=str, description="Device hostname"
))
AttributeRegistry.register(AttributeDescriptor(
    id="model", category=ObservationCategory.IDENTITY, value_type=str, description="Device model"
))
AttributeRegistry.register(AttributeDescriptor(
    id="device_type", category=ObservationCategory.IDENTITY, value_type=str, description="Device type"
))
AttributeRegistry.register(AttributeDescriptor(
    id="services", category=ObservationCategory.SERVICE, value_type=list, description="List of discovered services"
))
AttributeRegistry.register(AttributeDescriptor(
    id="open_ports", category=ObservationCategory.SERVICE, value_type=list, description="List of open TCP/UDP ports"
))
AttributeRegistry.register(AttributeDescriptor(
    id="ttl", category=ObservationCategory.CONNECTIVITY, value_type=int, description="Time To Live value"
))

__all__ = [
    "Observation", "UnifiedObservation", "ObservationMetadata", "ObservationCategory",
    "Normalizer", "RuleRegistry", "normalization_rule", "ObservationFactory", "AttributeRegistry"
]
