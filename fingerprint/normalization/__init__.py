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
AttributeRegistry.register(AttributeDescriptor(
    id="banner", category=ObservationCategory.SERVICE, value_type=str, description="Service banner string"
))
AttributeRegistry.register(AttributeDescriptor(
    id="os_version", category=ObservationCategory.IDENTITY, value_type=dict, description="OS version and protocol info"
))
AttributeRegistry.register(AttributeDescriptor(
    id="ntp_info", category=ObservationCategory.TIMING, value_type=dict, description="NTP stratum and reference info"
))
AttributeRegistry.register(AttributeDescriptor(
    id="http_services", category=ObservationCategory.SERVICE, value_type=dict, description="HTTP services per port"
))
AttributeRegistry.register(AttributeDescriptor(
    id="snmp_info", category=ObservationCategory.IDENTITY, value_type=dict, description="SNMP MIB-II data"
))
AttributeRegistry.register(AttributeDescriptor(
    id="ssdp_info", category=ObservationCategory.DISCOVERY, value_type=dict, description="SSDP/UPnP device info"
))
AttributeRegistry.register(AttributeDescriptor(
    id="netbios_info", category=ObservationCategory.IDENTITY, value_type=dict, description="NetBIOS computer name info"
))
AttributeRegistry.register(AttributeDescriptor(
    id="wsd_info", category=ObservationCategory.DISCOVERY, value_type=dict, description="WSD device discovery info"
))
AttributeRegistry.register(AttributeDescriptor(
    id="dns_sd_services", category=ObservationCategory.SERVICE, value_type=list, description="List of discovered DNS-SD services"
))
__all__ = [
    "Observation", "UnifiedObservation", "ObservationMetadata", "ObservationCategory",
    "Normalizer", "RuleRegistry", "normalization_rule", "ObservationFactory", "AttributeRegistry"
]
